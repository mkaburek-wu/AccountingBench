"""
AccountingBench — Real Benchmark Pipeline (Parallel)
=====================================================
Adapted from benchmark_run_v3_types_KopieV6.py.

All models run in parallel using ThreadPoolExecutor — each model gets its
own thread and its own database session. Total runtime is roughly equal to
the slowest single model instead of the sum of all models.

Key changes from the original script:
  - Reads the task from the database (benchmark_tasks) instead of Excel files.
  - Writes results to the database (benchmark_runs + benchmark_outputs)
    instead of evaluation_template.xlsx.
  - All models run in parallel via ThreadPoolExecutor.
  - Each thread has its own SQLAlchemy session (sessions are not thread-safe).
  - All core logic (LLM calls, scoring, judge, prompt building, attachment
    resolution) is kept identical to the original script.

To activate this pipeline, change one line in submissions.py:
    From: from backend.processing.dummy_pipeline import run_pipeline
    To:   from backend.processing.pipeline import run_pipeline

Environment variables required in .env:
    OPENAI_API_KEY          — OpenAI API key
    MODEL_REGISTRY_JSON     — Optional JSON for multi-endpoint / Azure Foundry
    OPENAI_MODEL_LIST       — Optional comma-separated list of models to run.
                              If not set, ALL_MODELS below is used.
"""

import hashlib
import json
import logging
import os
import re
import uuid
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import requests as req_lib
from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.models import BenchmarkOutput, BenchmarkRun, BenchmarkTask, Submission

try:
    import fitz as _fitz  # PyMuPDF — much more reliable than pypdf for real-world PDFs
except Exception:
    _fitz = None

try:
    from huggingface_hub import hf_hub_download
except Exception:
    hf_hub_download = None

try:
    from anthropic import AnthropicFoundry
except Exception:
    AnthropicFoundry = None

#load_dotenv()
from pathlib import Path
_ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=_ENV_PATH, override=False)


logger = logging.getLogger(__name__)


class InsufficientBalanceError(RuntimeError):
    """Raised when any provider returns an insufficient-balance error.
    Propagates out of run_pipeline so batch scripts can exit immediately."""


class IncompleteRunError(RuntimeError):
    """Raised when any model failed or was skipped for a task.
    All models must produce output for benchmark comparability.
    Propagates out of run_pipeline so batch scripts can stop cleanly,
    letting already-running parallel tasks finish before exiting."""

# ── Configuration ─────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

MODEL_REGISTRY_RAW = os.environ.get("MODEL_REGISTRY_JSON", "")
MODEL_REGISTRY: Dict[str, Dict[str, Any]] = {}
if MODEL_REGISTRY_RAW:
    try:
        MODEL_REGISTRY = json.loads(MODEL_REGISTRY_RAW)
        if not isinstance(MODEL_REGISTRY, dict):
            raise ValueError("MODEL_REGISTRY_JSON must be a JSON object/dict")
    except Exception as e:
        raise RuntimeError(f"Invalid MODEL_REGISTRY_JSON: {e}")

CLIENT_CACHE: Dict[str, Any] = {}

# Judge must stay fixed to gpt-5-mini for consistent benchmarking
JUDGE_MODEL = "gpt-5-mini"

SYSTEM_PROMPT_VERSION = "v3_types"
DATASET_VERSION       = "v3"
N_TRIALS              = 3

ATTACHMENTS_CACHE_DIR = ".attached_cache"
ATTACHMENTS_MAX_CHARS = 12000
HTTP_TIMEOUT_SEC      = 60

# ── Default model list ────────────────────────────────────────────────────────
# Can be overridden via OPENAI_MODEL_LIST in .env (comma-separated).
# To test with fewer models first, add to .env:
#   OPENAI_MODEL_LIST=gpt-4o,gpt-5-mini
ALL_MODELS = [
    "gpt-5.4",
    "gpt-5.2",
    "claude-opus-4-6",
    "claude-sonnet-4-6",
    "gpt-5-mini",
    "Mistral-Large-3",
    "grok-4-fast",
    "gpt-4o",
    "DeepSeek-V3.2-2",
    "mercury-2",
]

# Default OpenAI client — used when model is not in MODEL_REGISTRY
_openai_client = OpenAI(api_key=OPENAI_API_KEY, timeout=240.0)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS  (kept identical to original script)
# ─────────────────────────────────────────────────────────────────────────────
CHOICE_RE = re.compile(r"\b([A-Z])\b", re.IGNORECASE)


def safe_str(x: Any) -> str:
    if x is None:
        return ""
    s = str(x)
    return "" if s.lower() == "nan" else s


def normalize_task_type(primary: str, secondary: str, tertiary: str) -> str:
    """
    Determine the canonical task kind from answer_type (primary source of truth),
    task_format, and task_type fields.
    """
    key = (primary or "").strip().lower()
    if not key:
        key = (secondary or "").strip().lower()
    if not key:
        key = (tertiary or "").strip().lower()
    mapping = {
        "single_choice": "single_choice",
        "multi_choice":  "multi_choice",
        "open_text":     "open_text",
        "open_numeric":  "open_numeric",
        "journal_entry": "journal_entry",
    }
    return mapping.get(key, key)


def majority_vote(strings: List[str]) -> str:
    strings = [s for s in strings if s is not None and str(s).strip() != ""]
    if not strings:
        return ""
    cnt        = Counter(strings)
    top_count  = cnt.most_common(1)[0][1]
    candidates = {k for k, v in cnt.items() if v == top_count}
    for s in strings:
        if s in candidates:
            return s
    return strings[0]


def parse_choice_id(text: str, valid: Optional[List[str]] = None) -> Optional[str]:
    if not text:
        return None
    hits = [c.upper() for c in CHOICE_RE.findall(text.upper())]
    for c in hits:
        if valid is None or c in valid:
            return c
    return None


def parse_choice_set(text: str, valid: Optional[List[str]] = None) -> List[str]:
    if not text:
        return []
    hits      = [c.upper() for c in CHOICE_RE.findall(text.upper())]
    out, seen = [], set()
    for c in hits:
        if valid is not None and c not in valid:
            continue
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def gold_set(gold: str) -> List[str]:
    return [g.strip().upper() for g in str(gold).split(",") if g.strip()]


def score_sc_mc_percent(final_answer: str, gold: str) -> float:
    """SC/MC formula: unit * correct_marked - unit * incorrect_marked, clamped to [0, 100]."""
    gold_list = list(dict.fromkeys(gold_set(gold)))
    n         = len(gold_list)
    if n == 0:
        return 0.0
    fa = (final_answer or "").strip().upper()
    if not fa:
        return 0.0
    marked = (
        set(x.strip() for x in fa.split(",") if x.strip())
        if "," in fa else {fa}
    )
    gold_s           = set(gold_list)
    correct_marked   = len(marked.intersection(gold_s))
    incorrect_marked = len(marked.difference(gold_s))
    unit  = 100.0 / n
    score = unit * correct_marked - unit * incorrect_marked
    return max(0.0, min(100.0, score))


def parse_number(text: str) -> Optional[float]:
    if not text:
        return None
    s = text.strip()
    m = re.search(r"[-+]?\d[\d\s\.,]*\d|\b\d\b", s)
    if not m:
        return None
    token = m.group(0).replace(" ", "")
    if "." in token and "," in token:
        if token.rfind(",") > token.rfind("."):
            token = token.replace(".", "").replace(",", ".")
        else:
            token = token.replace(",", "")
    elif "," in token and "." not in token:
        token = token.replace(",", ".")
    try:
        return float(token)
    except Exception:
        return None


def within_tolerance(pred: float, gold: float, tol: Optional[float]) -> bool:
    if tol is None:
        return round(pred, 2) == round(gold, 2)
    return abs(pred - gold) <= tol


def parse_tolerance(x: Any) -> Optional[float]:
    if x is None:
        return None
    s = safe_str(x).strip()
    if not s:
        return None
    try:
        return float(s)
    except Exception:
        return parse_number(s)


# ─────────────────────────────────────────────────────────────────────────────
# ATTACHED DOCUMENT RESOLUTION  (kept identical to original)
# ─────────────────────────────────────────────────────────────────────────────
def _ensure_cache_dir() -> None:
    os.makedirs(ATTACHMENTS_CACHE_DIR, exist_ok=True)


def _split_attached_files(raw: str) -> List[str]:
    s = (raw or "").strip()
    if not s:
        return []
    parts   = re.split(r"[\n\r;,]+", s)
    cleaned = []
    for p in parts:
        u = (p.strip().strip('"').strip("'").strip()
              .lstrip("[").rstrip("]").strip().strip('"').strip("'").strip())
        if u:
            cleaned.append(u)
    return cleaned


def _cache_path_for_url(url: str) -> str:
    h = hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]
    return os.path.join(ATTACHMENTS_CACHE_DIR, f"{h}.bin")


def _try_hf_hub_download(url: str) -> Optional[str]:
    if hf_hub_download is None or "huggingface.co/datasets/" not in url:
        return None
    try:
        tail = url.split("/datasets/", 1)[1]
        m    = re.match(
            r"(?P<repo>[^/]+/[^/]+)/(?P<mode>resolve|raw)/(?P<rev>[^/]+)/(?P<path>.+)$",
            tail,
        )
        if not m:
            return None
        return hf_hub_download(
            repo_id=m.group("repo"), repo_type="dataset",
            filename=m.group("path"), revision=m.group("rev"),
        )
    except Exception:
        return None


def _to_hf_fetch_url(url: str) -> str:
    if "huggingface.co/datasets/" in url:
        if "/raw/" in url:
            url = url.replace("/raw/", "/resolve/", 1)
        if "?" not in url:
            return url + "?download=1"
        if "download=" not in url:
            return url + "&download=1"
    return url


def _is_git_lfs_pointer(data: bytes) -> bool:
    head = data[:200].decode("utf-8", errors="ignore")
    return head.lstrip().startswith("version https://git-lfs.github.com/spec/v1")


def _strip_wrappers(s: str) -> str:
    return (s or "").strip().strip('"').strip("'")


def _normalize_local_path(s: str) -> str:
    s = _strip_wrappers(s)
    if s.lower().startswith("file://"):
        s = s[7:].lstrip("/")
    return s


def _looks_like_local_path(s: str) -> bool:
    s = _strip_wrappers(s)
    if not s:
        return False
    if re.match(r"^[a-zA-Z]:\\", s) or s.startswith("\\\\"):
        return True
    if re.match(r"^https?://", s, flags=re.IGNORECASE):
        return False
    if os.path.exists(s):
        return True
    if ("/" in s or "\\" in s) and "://" not in s:
        return True
    return False


def _download_url_to_cache(url: str) -> str:
    _ensure_cache_dir()
    local_path = _normalize_local_path(url)
    if _looks_like_local_path(local_path):
        if os.path.exists(local_path):
            return local_path
        raise FileNotFoundError(f"Local attached file not found: {local_path}")
    hf_path = _try_hf_hub_download(url)
    if hf_path:
        return hf_path
    out_path = _cache_path_for_url(url)
    if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
        return out_path
    fetch_url = _to_hf_fetch_url(url)
    headers   = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept":     "application/pdf,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,de;q=0.8",
    }
    r = req_lib.get(fetch_url, headers=headers, allow_redirects=True, timeout=HTTP_TIMEOUT_SEC)
    r.raise_for_status()
    if "huggingface.co/datasets/" in url and _is_git_lfs_pointer(r.content):
        alt_url = _to_hf_fetch_url(url.replace("/raw/", "/resolve/", 1))
        r       = req_lib.get(alt_url, headers=headers, allow_redirects=True, timeout=HTTP_TIMEOUT_SEC)
        r.raise_for_status()
    ctype = (r.headers.get("content-type") or "").lower()
    if "text/html" in ctype and fetch_url != url:
        r = req_lib.get(url, headers=headers, allow_redirects=True, timeout=HTTP_TIMEOUT_SEC)
        r.raise_for_status()
    with open(out_path, "wb") as f:
        f.write(r.content)
    return out_path


def _pdf_bytes_to_text(pdf_bytes: bytes) -> str:
    if _fitz is None:
        raise RuntimeError("PyMuPDF not available. Install: pip install pymupdf")
    doc = _fitz.open(stream=pdf_bytes, filetype="pdf")
    texts = [page.get_text() for page in doc]
    return "\n\n".join(t for t in texts if t.strip()).strip()


def _truncate_text(text: str, max_chars: int) -> str:
    t = (text or "").strip()
    if not t or len(t) <= max_chars:
        return t
    head = t[: int(max_chars * 0.75)]
    tail = t[-int(max_chars * 0.20):]
    return head.rstrip() + "\n\n[... gekürzt ...]\n\n" + tail.lstrip()


def resolve_attached_documents_text(attached_raw: str) -> str:
    urls = _split_attached_files(attached_raw)
    if not urls:
        return ""
    chunks = []
    for idx, url in enumerate(urls, start=1):
        try:
            cache_path = _download_url_to_cache(url)
            with open(cache_path, "rb") as f:
                data = f.read()
            if data[:4] == b"%PDF":
                txt = _pdf_bytes_to_text(data)
                txt = _truncate_text(txt, ATTACHMENTS_MAX_CHARS)
                char_count = len(txt) if txt else 0
                logger.info(
                    f"[attachment {idx}/{len(urls)}] loaded PDF: {url!r} "
                    f"({len(data)} bytes → {char_count} chars)"
                )
                if not txt:
                    raise RuntimeError(
                        f"PDF_NO_TEXT: attachment {url!r} yielded no extractable text "
                        f"({len(data)} bytes). The file is likely a scanned image PDF "
                        f"with no text layer."
                    )
                chunks.append(f"[DOKUMENT {idx}] Quelle: {url}\n\n{txt}")
            else:
                snippet = _truncate_text(data[:4000].decode("utf-8", errors="replace"), 4000)
                logger.info(
                    f"[attachment {idx}/{len(urls)}] loaded non-PDF: {url!r} "
                    f"({len(data)} bytes)"
                )
                chunks.append(f"[DOKUMENT {idx}] Quelle: {url}\n\n(Kein PDF. Snippet:)\n{snippet}")
        except Exception as e:
            logger.error(
                f"[attachment {idx}/{len(urls)}] failed to load: {url!r} — "
                f"{type(e).__name__}: {e}"
            )
            raise
    return ("\n\n" + "-" * 40 + "\n\n").join(chunks).strip()


# ─────────────────────────────────────────────────────────────────────────────
# JSON EXTRACTION  (kept identical)
# ─────────────────────────────────────────────────────────────────────────────
def extract_json_object(text: str) -> str:
    if not text:
        return ""
    t = text.strip()
    t = re.sub(r"^```(?:json)?\s*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s*```$", "", t)
    try:
        json.loads(t)
        return t
    except Exception:
        pass
    m = re.search(r"\{.*\}", t, flags=re.DOTALL)
    return m.group(0) if m else t


# ─────────────────────────────────────────────────────────────────────────────
# PROMPT BUILDERS  (adapted to use BenchmarkTask instead of pd.Series)
# ─────────────────────────────────────────────────────────────────────────────
def format_options(options_val: Any) -> str:
    s = safe_str(options_val).strip()
    if not s:
        return ""
    try:
        parsed = json.loads(s)
        if isinstance(parsed, dict):
            return "\n".join([f"{k}) {v}" for k, v in parsed.items()])
    except Exception:
        pass
    return s


def build_trial_prompt(task: BenchmarkTask) -> str:
    """
    Builds the trial prompt from a BenchmarkTask database row.
    Equivalent to the original build_trial_prompt(row: pd.Series).
    All prompt text is identical to the original script.
    """
    prompt   = safe_str(task.prompt).strip()
    context  = safe_str(task.context).strip()
    options  = format_options(task.options)
    attached = safe_str(task.attached_files).strip()

    parts = []
    if context:
        parts.append("KONTEXT:\n" + context)
    if attached:
        doc_text = resolve_attached_documents_text(attached)
        if doc_text:
            parts.append("DOKUMENT-INHALT (extrahiert):\n" + doc_text)
        else:
            parts.append("DOKUMENT-LINK (falls relevant):\n" + attached)

    parts.append("FRAGE:\n" + prompt)

    if options:
        parts.append("OPTIONEN:\n" + options)

    parts.append(
        "\nGIB AUSSCHLIESSLICH JSON ZURÜCK:\n"
        '{"answer": "...", "confidence": 0.0}\n'
        "confidence zwischen 0 und 1.\n"
        "Kein zusätzlicher Text."
    )
    return "\n\n".join(parts)


def build_open_final_prompt(question: str, a1: str, a2: str, a3: str) -> str:
    return (
        "Konsolidiere 3 Entwürfe zu einer finalen Antwort.\n"
        "Gib ausschließlich JSON zurück:\n"
        '{"answer": "...", "confidence": 0.0}\n'
        "confidence zwischen 0 und 1.\n\n"
        f"FRAGE:\n{question}\n\n"
        f"ENTWURF 1:\n{a1}\n\n"
        f"ENTWURF 2:\n{a2}\n\n"
        f"ENTWURF 3:\n{a3}\n"
    )


def build_judge_prompt(
    question: str,
    final_answer: str,
    gold_answer: str,
    grading_criteria: str = "",
    acceptable_variants: str = "",
    numeric_tol: Optional[float] = None,
) -> str:
    parts = [
        "Du bist ein strenger Evaluator für Accounting-Antworten.\n"
        "Vergleiche STUDENT_ANSWER mit GOLD_ANSWER und bewerte die Korrektheit.\n"
        "Gib ausschließlich JSON zurück:\n"
        '{"score_percent": 0, "confidence": 0.0, "notes": ""}\n'
        "- score_percent ist 0..100\n"
        "- confidence ist 0..1\n"
        "- notes max 200 Zeichen",
        f"FRAGE:\n{question}",
        f"GOLD_ANSWER:\n{gold_answer}",
    ]
    if acceptable_variants:
        parts.append(f"AKZEPTABLE VARIANTEN:\n{acceptable_variants}")
    if numeric_tol is not None:
        parts.append(
            f"NUMERISCHE TOLERANZ: ±{numeric_tol} "
            f"(Antworten innerhalb dieser Toleranz gelten als vollständig korrekt)"
        )
    if grading_criteria:
        parts.append(f"BEWERTUNGSKRITERIEN:\n{grading_criteria}")
    parts.append(f"STUDENT_ANSWER:\n{final_answer}")
    return "\n\n".join(parts)


# ─────────────────────────────────────────────────────────────────────────────
# API CALLS  (kept identical to original)
# ─────────────────────────────────────────────────────────────────────────────
def _is_responses_only_model(model: str) -> bool:
    m = (model or "").strip()
    if "-chat" in m:
        return False
    if MODEL_REGISTRY and model in MODEL_REGISTRY:
        base = (MODEL_REGISTRY[model].get("base_url") or "").lower()
        if "openai.azure.com" not in base and "api.openai.com" not in base:
            return False
    return m.startswith("gpt-5") or m.startswith("o")


def _reasoning_for_model(model: str):
    m = (model or "").strip()
    if m == "gpt-5.2-pro":
        return {"effort": "medium"}
    if m.endswith("-pro"):
        return {"effort": "high"}
    if m.startswith("gpt-5") or m.startswith("o"):
        return {"effort": "low"}
    return None


def _resolve_api_key(key: str) -> str:
    """Resolve ${ENV_VAR} references in api_key values from MODEL_REGISTRY_JSON."""
    if key and key.startswith("${") and key.endswith("}"):
        return os.environ.get(key[2:-1], key)
    return key


def _get_client_for_model(model: str) -> Tuple[Any, str]:
    if not MODEL_REGISTRY or model not in MODEL_REGISTRY:
        return _openai_client, "openai_default"
    cfg       = MODEL_REGISTRY.get(model) or {}
    api_type  = (cfg.get("api_type") or "").strip().lower()
    cache_key = f"{api_type}:{model}"
    if cache_key in CLIENT_CACHE:
        return CLIENT_CACHE[cache_key]
    if api_type == "openai_v1":
        base_url = cfg.get("base_url")
        api_key  = cfg.get("api_key")
        if not base_url or not api_key:
            raise RuntimeError(f"MODEL_REGISTRY entry for '{model}' missing base_url/api_key")
        # Allow per-model timeout override via MODEL_REGISTRY_JSON "timeout" key
        timeout  = float(cfg.get("timeout", 240.0))
        c = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout, max_retries=0)
        CLIENT_CACHE[cache_key] = (c, "openai_v1")
        return CLIENT_CACHE[cache_key]
    if api_type == "anthropic_foundry":
        base_url = cfg.get("base_url")
        api_key  = cfg.get("api_key")
        if not base_url or not api_key:
            raise RuntimeError(f"MODEL_REGISTRY entry for '{model}' missing base_url/api_key")
        if AnthropicFoundry is None:
            raise RuntimeError("anthropic SDK not installed. pip install -U anthropic")
        c = AnthropicFoundry(api_key=api_key, base_url=base_url)
        CLIENT_CACHE[cache_key] = (c, "anthropic_foundry")
        return CLIENT_CACHE[cache_key]
    if api_type == "alawyer":
        base_url = cfg.get("base_url", "https://app.alawyer.ai")
        api_key  = _resolve_api_key(cfg.get("api_key", ""))
        if not api_key:
            raise RuntimeError(
                f"MODEL_REGISTRY entry for '{model}': api_key is empty. "
                "Set ALAWYER_API_KEY in .env."
            )
        resolved_cfg = {
            "base_url": base_url,
            "api_key":  api_key,
            "timeout":  float(cfg.get("timeout", 660.0)),
        }
        CLIENT_CACHE[cache_key] = (resolved_cfg, "alawyer")
        return CLIENT_CACHE[cache_key]
    raise RuntimeError(f"Unsupported api_type for model '{model}': {api_type}")


def _get_timeout_for_model(model: str) -> float:
    """Return the configured timeout for a model (from MODEL_REGISTRY) or the default 240s."""
    if MODEL_REGISTRY and model in MODEL_REGISTRY:
        cfg = MODEL_REGISTRY.get(model) or {}
        return float(cfg.get("timeout", 240.0))
    return 240.0


def _get_model_api_id(model: str) -> str:
    """Return the model ID to send to the API.
    Allows overriding via 'model_id' in MODEL_REGISTRY_JSON — useful when the
    registry key (e.g. 'gpt-5-mini') differs from the provider's model name."""
    if MODEL_REGISTRY and model in MODEL_REGISTRY:
        return MODEL_REGISTRY[model].get("model_id") or model
    return model


def usage_to_tokens(usage_obj: Any) -> Tuple[Optional[int], Optional[int], Optional[int]]:
    if usage_obj is None:
        return None, None, None
    try:
        usage = usage_obj.model_dump() if hasattr(usage_obj, "model_dump") else dict(usage_obj)
    except Exception:
        return None, None, None
    if not isinstance(usage, dict):
        return None, None, None

    def _first(*keys):
        for k in keys:
            if k in usage and usage.get(k) is not None:
                return usage.get(k)
        return None

    token_in     = _first("prompt_tokens", "input_tokens", "promptTokens", "inputTokens")
    token_out    = _first("completion_tokens", "output_tokens", "completionTokens", "outputTokens")
    token_reason = None
    ctd = usage.get("completion_tokens_details")
    if isinstance(ctd, dict):
        token_reason = ctd.get("reasoning_tokens", ctd.get("reasoningTokens"))
    if token_reason is None:
        otd = usage.get("output_tokens_details")
        if isinstance(otd, dict):
            token_reason = otd.get("reasoning_tokens", otd.get("reasoningTokens"))
    if token_reason is None:
        token_reason = _first("reasoning_tokens", "reasoningTokens")

    def to_int(x):
        try:
            return int(x)
        except Exception:
            return None

    return to_int(token_in), to_int(token_out), to_int(token_reason)


def call_llm_json(
    prompt: str, model: str, temperature: float = 0.0
) -> Tuple[str, Optional[float], Tuple]:
    resolved_client, api_mode = _get_client_for_model(model)
    logger.debug(f"[LLM→] model={model} | prompt ({len(prompt)} chars):\n{prompt}")

    # Anthropic via Azure Foundry
    _timeout = _get_timeout_for_model(model)
    if api_mode == "anthropic_foundry":
        resp     = resolved_client.messages.create(
            model=model,
            system="Gib strikt nur JSON aus. Kein anderer Text.",
            max_tokens=30000,
            messages=[{"role": "user", "content": prompt}],
            timeout=_timeout,
        )
        raw_text = resp.content[0].text if getattr(resp, "content", None) else ""
        text     = extract_json_object(raw_text)
        answer, conf = "", None
        try:
            data     = json.loads(text)
            raw_answer = data.get("answer", "")
            if isinstance(raw_answer, (dict, list)):
                # Model returned structured JSON instead of a string — serialize it back to text
                import json as _json
                answer = _json.dumps(raw_answer, ensure_ascii=False)
            elif raw_answer is None or raw_answer == "":
                # Model put content at top level instead of under "answer" key
                # Re-serialize the whole object minus "confidence"
                top_level = {k: v for k, v in data.items() if k != "confidence"}
                answer = _json.dumps(top_level, ensure_ascii=False)
            else:
                answer = str(raw_answer).strip()

            conf_val = data.get("confidence", None)
            conf     = max(0.0, min(1.0, float(conf_val))) if conf_val is not None else None
        except Exception:
            answer = raw_text.strip()
        try:
            u         = getattr(resp, "usage", None)
            token_in  = getattr(u, "input_tokens",  None) if u else None
            token_out = getattr(u, "output_tokens", None) if u else None
        except Exception:
            token_in = token_out = None
        logger.debug(f"[LLM←] model={model} | raw={raw_text!r}")
        logger.debug(f"[LLM←] model={model} | answer={answer!r} conf={conf}")
        return answer, conf, (token_in, token_out, None)

    # Alawyer — Austrian legal AI (SSE streaming, custom endpoint)
    # Docs: Alawyer_API_Docs_030626.pdf — POST /api/v1/completions
    # Supports native json_schema response_format — no secondary extraction call needed.
    # Rate limit: 10 req/min. Use --max-workers 1 or 2 when running rerun_model.
    if api_mode == "alawyer":
        cfg      = resolved_client  # config dict stored in CLIENT_CACHE
        base_url = cfg["base_url"].rstrip("/")
        api_key  = cfg["api_key"]
        timeout  = cfg["timeout"]

        # Strip the JSON format instruction appended by build_trial_prompt —
        # response_format handles that natively; the instruction confuses the model.
        alawyer_query = re.split(r"\nGIB AUSSCHLIESSLICH JSON ZURÜCK", prompt)[0].strip()
        # Add explicit selection hint for choice questions: alawyer has no system prompt
        # and no format instruction, so without this it lists all options in the answer field.
        alawyer_query += (
            "\n\nFalls die Frage Auswahloptionen (A, B, C ...) enthält, gib im Feld \"answer\" "
            "NUR die Buchstabe(n) der richtigen Antwort(en) an, kommagetrennt "
            "(z.B. \"A\" oder \"A,C\"). Kein erklärender Text im answer-Feld."
        )

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type":  "application/json",
            "Accept":        "text/event-stream",
        }
        resp = req_lib.post(
            f"{base_url}/api/v1/completions",
            headers=headers,
            json={
                "query": alawyer_query,
                "mode":  "max",
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "legal_answer",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "answer": {
                                    "type": "string",
                                    "description": (
                                        "For multiple-choice questions: ONLY the correct letter(s), "
                                        "comma-separated (e.g. 'A' or 'A,C'). "
                                        "For single-choice: the one correct letter (e.g. 'B'). "
                                        "For open questions: concise answer text."
                                    ),
                                },
                                "confidence": {
                                    "type": "number",
                                    "description": "Confidence in the answer, between 0 and 1.",
                                },
                            },
                            "required": ["answer", "confidence"],
                            "additionalProperties": False,
                        },
                    },
                },
            },
            timeout=timeout,
            stream=True,
        )
        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", "60"))
            raise RuntimeError(f"Alawyer rate limit exceeded — retry after {retry_after}s")
        resp.raise_for_status()

        # SSE: accumulate data: fields per event (blank line = event boundary).
        # Alawyer may embed raw newlines in the response string, which iter_lines()
        # splits into continuation lines — treat them as part of the same event.
        payload = None
        received_lines: list[str] = []
        event_data: list[str] = []
        in_data_field = False

        for line in resp.iter_lines(decode_unicode=True):
            if line is None:
                continue
            if not line:
                # Blank line = SSE event boundary — flush accumulated data
                if event_data:
                    raw = "\n".join(event_data)
                    if raw == "[DONE]":
                        break
                    try:
                        payload = json.loads(raw)
                    except json.JSONDecodeError as ex:
                        # Alawyer embeds raw newlines in string values — escape them
                        try:
                            fixed = raw.replace('\r\n', '\\n').replace('\r', '\\n').replace('\n', '\\n')
                            payload = json.loads(fixed)
                            logger.warning(f"[alawyer] JSON had raw newlines, fixed: {ex}")
                        except json.JSONDecodeError:
                            logger.warning(f"[alawyer] JSON parse error: {ex} | raw[:300]={raw[:300]!r}")
                    event_data = []
                    in_data_field = False
                continue
            if line.startswith(":"):
                continue  # SSE keepalive / comment
            received_lines.append(line)
            if line == "data: [DONE]":
                break
            if line.startswith("data: "):
                event_data.append(line[6:])
                in_data_field = True
            elif in_data_field:
                # Continuation: raw newline in data: value split by iter_lines()
                event_data.append(line)

        # Flush remaining event if stream ended without a trailing blank line
        if event_data and payload is None:
            raw = "\n".join(event_data)
            if raw != "[DONE]":
                try:
                    payload = json.loads(raw)
                except json.JSONDecodeError as ex:
                    try:
                        fixed = raw.replace('\r\n', '\\n').replace('\r', '\\n').replace('\n', '\\n')
                        payload = json.loads(fixed)
                        logger.warning(f"[alawyer] JSON had raw newlines (eof), fixed: {ex}")
                    except json.JSONDecodeError:
                        logger.warning(f"[alawyer] JSON parse error (eof): {ex} | raw[:300]={raw[:300]!r}")

        if payload is None:
            logger.warning(
                f"[alawyer] No data event in SSE response. "
                f"Lines received: {received_lines[:5]!r}"
            )
            raise RuntimeError("Alawyer: no data event received in SSE response")
        if "error" in payload:
            err = payload["error"]
            # empty_answer means Alawyer had no result for this query — treat as
            # an empty response (score 0) rather than a fatal pipeline error.
            if isinstance(err, dict) and err.get("message") == "empty_answer":
                logger.warning("[alawyer] empty_answer — no result for this query, returning empty")
                return "", None, (None, None, None)
            raise RuntimeError(f"Alawyer upstream error: {payload['error']}")

        raw_response = (payload.get("response") or "").strip()
        usage        = payload.get("usage") or {}
        token_in     = usage.get("prompt_tokens")
        token_out    = usage.get("completion_tokens")

        logger.debug(f"[LLM←] alawyer | raw_response={raw_response[:200]!r}")

        # In json_schema mode, response is a JSON-encoded string — parse directly.
        # The inner response may also contain literal newlines inside string values
        # (same issue as the outer SSE data), so apply the same fix as a fallback.
        answer = ""
        conf   = None
        try:
            result = json.loads(raw_response)
        except json.JSONDecodeError:
            try:
                fixed = raw_response.replace('\r\n', '\\n').replace('\r', '\\n').replace('\n', '\\n')
                result = json.loads(fixed)
                logger.warning(f"[alawyer] json_schema response had raw newlines, fixed")
            except json.JSONDecodeError:
                logger.warning(f"[alawyer] Could not parse json_schema response, using raw text: {raw_response[:200]!r}")
                result = None
        try:
            if result is not None:
                answer = str(result.get("answer", "")).strip()
                conf_val = result.get("confidence")
                if conf_val is not None:
                    conf = max(0.0, min(1.0, float(conf_val)))
        except (ValueError, TypeError):
            logger.warning(f"[alawyer] Could not extract answer from parsed response: {result!r}")
            answer = raw_response

        return answer, conf, (token_in, token_out, None)

    # GPT-5 / o-series — use Responses API
    if _is_responses_only_model(model):
        reasoning_cfg = _reasoning_for_model(model)
        kwargs = {
            "model": _get_model_api_id(model),
            "input": [
                {"role": "system", "content": "Gib strikt nur JSON aus. Kein anderer Text."},
                {"role": "user",   "content": prompt},
            ],
        }
        if reasoning_cfg:
            kwargs["reasoning"] = reasoning_cfg
        resp     = resolved_client.responses.create(**kwargs, timeout=_timeout)
        raw_text = getattr(resp, "output_text", "") or ""
    else:
        # Chat completions
        if model == "gpt-5.2-chat":
            resp = resolved_client.chat.completions.create(
                model=_get_model_api_id(model),
                timeout=_timeout,
                messages=[
                    {"role": "system", "content": "Gib strikt nur JSON aus. Kein anderer Text."},
                    {"role": "user",   "content": prompt},
                ],
            )
        else:
            cfg        = MODEL_REGISTRY.get(model) or {}
            extra_body = dict(cfg.get("extra_body") or {})
            if cfg.get("allowed_providers"):
                extra_body["allowed_providers"] = cfg["allowed_providers"]
            kwargs: dict = {
                "model":      _get_model_api_id(model),
                "timeout":    _timeout,
                "messages":   [
                    {"role": "system", "content": "Gib strikt nur JSON aus. Kein anderer Text."},
                    {"role": "user",   "content": prompt},
                ],
                "extra_body": extra_body or None,
            }
            if not cfg.get("no_temperature"):
                kwargs["temperature"] = temperature
            resp = resolved_client.chat.completions.create(**kwargs)
        raw_text = resp.choices[0].message.content or ""

    text         = extract_json_object(raw_text)
    answer, conf = "", None
    try:
        data     = json.loads(text)
        raw_answer = data.get("answer", "")
        if isinstance(raw_answer, (dict, list)):
            # Model returned structured JSON instead of a string — serialize it back to text
            import json as _json
            answer = _json.dumps(raw_answer, ensure_ascii=False)
        elif raw_answer is None or raw_answer == "":
            # Model put content at top level instead of under "answer" key
            # Re-serialize the whole object minus "confidence"
            top_level = {k: v for k, v in data.items() if k != "confidence"}
            answer = _json.dumps(top_level, ensure_ascii=False)
        else:
            answer = str(raw_answer).strip()

        conf_val = data.get("confidence", None)
        conf     = max(0.0, min(1.0, float(conf_val))) if conf_val is not None else None
    except Exception:
        answer = raw_text.strip()

    token_in, token_out, token_reason = usage_to_tokens(getattr(resp, "usage", None))
    logger.debug(f"[LLM←] model={model} | raw={raw_text!r}")
    logger.debug(f"[LLM←] model={model} | answer={answer!r} conf={conf}")
    return answer, conf, (token_in, token_out, token_reason)


def call_judge(
    question: str,
    final_answer: str,
    gold_answer: str,
    grading_criteria: str = "",
    acceptable_variants: str = "",
    numeric_tol: Optional[float] = None,
) -> Tuple[float, Optional[float], str, Optional[int], Optional[int]]:
    resolved_client, api_mode = _get_client_for_model(JUDGE_MODEL)
    if api_mode == "anthropic_foundry":
        raise RuntimeError("JUDGE_MODEL must be an OpenAI-compatible deployment.")

    prompt = build_judge_prompt(
        question, final_answer, gold_answer,
        grading_criteria=grading_criteria,
        acceptable_variants=acceptable_variants,
        numeric_tol=numeric_tol,
    )

    if _is_responses_only_model(JUDGE_MODEL):
        resp     = resolved_client.responses.create(
            model=_get_model_api_id(JUDGE_MODEL),
            reasoning={"effort": "low"},
            input=[
                {"role": "system", "content": "Gib strikt nur JSON aus. Kein anderer Text."},
                {"role": "user",   "content": prompt},
            ],
        )
        raw_text = getattr(resp, "output_text", "") or "{}"
    else:
        resp     = resolved_client.chat.completions.create(
            model=_get_model_api_id(JUDGE_MODEL),
            temperature=0.0,
            messages=[
                {"role": "system", "content": "Gib strikt nur JSON aus. Kein anderer Text."},
                {"role": "user",   "content": prompt},
            ],
        )
        raw_text = resp.choices[0].message.content or "{}"

    j_in, j_out, _ = usage_to_tokens(getattr(resp, "usage", None))

    text = extract_json_object(raw_text)
    try:
        data          = json.loads(text)
        score_percent = max(0.0, min(100.0, float(data.get("score_percent", 0.0))))
        conf_val      = data.get("confidence", None)
        conf          = max(0.0, min(1.0, float(conf_val))) if conf_val is not None else None
        notes         = str(data.get("notes", "") or "")[:200]
        return score_percent, conf, notes, j_in, j_out
    except Exception:
        return 0.0, None, "judge_parse_error", j_in, j_out


# ─────────────────────────────────────────────────────────────────────────────
# MAIN PIPELINE FUNCTION
# ─────────────────────────────────────────────────────────────────────────────
def run_pipeline(submission_id: int, db: Session = None) -> None:
    """
    Real benchmark pipeline — runs all models in parallel against a single task.

    Each model runs in its own thread with its own database session.
    SQLAlchemy sessions are not thread-safe, so sharing one session across
    threads would cause errors. Each thread creates, uses, and closes its own.

    Called as a FastAPI BackgroundTask from submissions.py:
        background_tasks.add_task(run_pipeline, submission.id)

    Reads:   benchmark_tasks (via submission.task_id)
    Writes:  benchmark_runs + benchmark_outputs (one row per model each)
    Updates: submissions.status → processing → done | error
    """
    if not OPENAI_API_KEY and not MODEL_REGISTRY:
        raise RuntimeError("No API key set. Add OPENAI_API_KEY or MODEL_REGISTRY_JSON to .env")

    close_db = False
    if db is None:
        db       = SessionLocal()
        close_db = True

    try:
        # ── 1. Mark as processing ─────────────────────────────────────────────
        submission = db.query(Submission).filter_by(id=submission_id).first()
        if not submission:
            logger.error(f"Submission {submission_id} not found.")
            return

        submission.status = "processing"
        db.commit()
        logger.info(f"[PIPELINE] Submission {submission_id} — processing started.")

        # ── 2. Load the task from the database ────────────────────────────────
        task = db.query(BenchmarkTask).filter_by(id=submission.task_id).first()
        if not task:
            raise ValueError(f"BenchmarkTask not found for submission {submission_id}")

        # Snapshot the task fields we need — the task object must not cross
        # thread boundaries (SQLAlchemy objects are not thread-safe either).
        task_id             = task.id
        task_prompt         = safe_str(task.prompt).strip()
        task_context        = safe_str(task.context).strip()
        task_options        = task.options
        task_attached       = safe_str(task.attached_files).strip()
        gold_answer         = safe_str(task.gold_answer).strip()
        numeric_tol         = parse_tolerance(task.numeric_tolerance)
        grading_criteria    = safe_str(task.grading_criteria).strip()
        acceptable_variants = safe_str(task.acceptable_variants).strip()

        kind = normalize_task_type(
            safe_str(task.answer_type),
            safe_str(task.task_format),
            safe_str(task.task_type),
        )

        # Parse valid choices for SC/MC tasks.
        # task_options is already a Python dict (SQLAlchemy deserialises JSON columns),
        # so we use it directly instead of round-tripping through json.loads(str(...))
        # which produces invalid JSON from Python's single-quoted repr.
        valid_choices = None
        if task_options:
            try:
                parsed = task_options if isinstance(task_options, dict) else json.loads(task_options)
                if isinstance(parsed, dict):
                    valid_choices = [str(k).upper() for k in parsed.keys()]
            except Exception:
                valid_choices = None

        # ── 3. Determine which models to run ──────────────────────────────────
        model_list_raw = os.environ.get("OPENAI_MODEL_LIST", "")
        models_to_run  = (
            [m.strip() for m in model_list_raw.split(",") if m.strip()]
            or ALL_MODELS
        )

        # ── 4. Shared run_id for this benchmark run ───────────────────────────
        run_id  = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        now_utc = datetime.now(timezone.utc)

        # ── 5. Define the per-model worker function ───────────────────────────
        def run_single_model(current_model: str) -> str:
            """
            Runs one model against the task and writes its results to the database.
            Returns the model name on success, or "ERROR:{model_name}" on failure.

            Each call creates its own database session — sessions are not thread-safe.
            The task fields are accessed from the closure (immutable snapshots above).
            """
            # Create a dedicated session for this thread
            thread_db = SessionLocal()
            try:
                logger.info(f"[PIPELINE] [{current_model}] Starting...")

                # Insert run metadata
                run = BenchmarkRun(
                    run_id                = run_id,
                    task_id               = task_id,
                    model_name            = current_model,
                    run_timestamp         = now_utc,
                    temperature           = 0.0,
                    n_trials              = N_TRIALS,
                    system_prompt_version = SYSTEM_PROMPT_VERSION,
                    dataset_version       = DATASET_VERSION,
                    judge_model           = JUDGE_MODEL,
                    inference_notes       = f"N_TRIALS={N_TRIALS}; JUDGE_MODEL={JUDGE_MODEL}; parallel=True",
                )
                thread_db.add(run)

                # Build a minimal task-like object for build_trial_prompt.
                # We use a simple namespace instead of the ORM object to
                # avoid crossing the session boundary.
                class _TaskProxy:
                    prompt        = task_prompt
                    context       = task_context
                    options       = task_options
                    attached_files = task_attached

                task_proxy = _TaskProxy()

                # ── 3 trials ──────────────────────────────────────────────────
                trial_answers, trial_confs = [], []
                token_input = token_output = token_reasoning = None

                
                for t in range(1, N_TRIALS + 1):
                    logger.info(f"  [{current_model}] Trial {t}...")
                    trial_prompt = build_trial_prompt(task_proxy)

                    # Retry once on transient errors (429, 500, 503)
                    # Skip immediately on permanent errors (404)
                    trial_needed_retry = False
                    for attempt in range(2):
                        try:
                            ans, conf, (t_in, t_out, t_reason) = call_llm_json(
                                trial_prompt, model=current_model, temperature=0.0
                            )
                            break  # success — exit retry loop

                        except Exception as e:
                            error_str    = str(e)
                            if 'Insufficient Balance' in error_str:
                                if attempt == 0:
                                    # Retry once — Cortecs occasionally returns false balance errors
                                    logger.warning(
                                        f"  [{current_model}] Trial {t} — 'Insufficient Balance' "
                                        f"(may be transient), retrying in 30s: {e}"
                                    )
                                    trial_needed_retry = True
                                    time.sleep(30)
                                    continue
                                raise InsufficientBalanceError(
                                    f"[{current_model}] Insufficient balance confirmed after retry — stopping run."
                                ) from e
                            is_not_found = '404' in error_str or 'DeploymentNotFound' in error_str
                            is_alawyer   = any(s in error_str for s in [
                                'no data event', 'Read timed out', 'ConnectionError',
                                'RemoteDisconnected', 'Connection reset',
                            ])
                            is_timeout   = 'timed out' in error_str.lower()
                            is_transient = is_alawyer or is_timeout or any(c in error_str for c in ['429', '500', '502', '503'])

                            if is_not_found:
                                logger.warning(
                                    f"  [{current_model}] Deployment not found (404) — "
                                    f"skipping. Remove from OPENAI_MODEL_LIST or fix MODEL_REGISTRY_JSON."
                                )
                                return f"SKIP:{current_model}"

                            elif attempt == 0 and is_transient:
                                is_rate_limited = '429' in error_str
                                delay = 30 if is_alawyer else 60 if is_rate_limited else 5
                                logger.warning(
                                    f"  [{current_model}] Trial {t} transient error, "
                                    f"retrying in {delay}s: {e}"
                                )
                                trial_needed_retry = True
                                time.sleep(delay)
                            else:
                                raise  # permanent error or retry also failed

                    if trial_needed_retry:
                        raise RuntimeError(
                            f"[{current_model}] Trial {t} required a retry — "
                            f"stopping model run to preserve benchmark integrity. "
                            f"Rerun this task once the model is stable."
                        )

                    if t == 1:
                        token_input     = t_in
                        token_output    = t_out
                        token_reasoning = t_reason

                    # Parse answer based on task kind
                    if kind == "single_choice":
                        ans = parse_choice_id(ans, valid=valid_choices) or ""
                    elif kind == "multi_choice":
                        ans = ",".join(parse_choice_set(ans, valid=valid_choices))
                    elif kind == "open_numeric":
                        ans = ans.strip()

                    trial_answers.append(ans)
                    trial_confs.append(conf)




                conf_vals = [c for c in trial_confs if isinstance(c, (int, float))]
                avg_conf  = (sum(conf_vals) / len(conf_vals)) if conf_vals else None

                # ── Score and evaluate ────────────────────────────────────────
                final_answer        = ""
                eval_method         = ""
                sc_mc_score_percent = None
                judge_score_percent = None
                judge_conf          = None
                judge_tok_in        = None
                judge_tok_out       = None
                notes               = ""
                final_score         = None

                if kind in ("single_choice", "multi_choice"):
                    final_answer        = majority_vote(trial_answers)
                    sc_mc_score_percent = score_sc_mc_percent(final_answer, gold_answer)
                    eval_method         = "sc_mc_formula"
                    notes               = f"Final=majority(trials); score=SC/MC formula; kind={kind}"
                    final_score         = sc_mc_score_percent

                else:
                    # Open text / open numeric / journal entry
                    logger.info(f"  [{current_model}] Final consolidation call...")
                    final_prompt  = build_open_final_prompt(
                        task_prompt,
                        trial_answers[0] if len(trial_answers) > 0 else "",
                        trial_answers[1] if len(trial_answers) > 1 else "",
                        trial_answers[2] if len(trial_answers) > 2 else "",
                    )
                    final_answer, _, _ = call_llm_json(
                        final_prompt, model=current_model, temperature=0.0
                    )
                    logger.info(f"  [{current_model}] Judge call...")
                    judge_score_percent, judge_conf, jnotes, judge_tok_in, judge_tok_out = call_judge(
                        task_prompt, final_answer, gold_answer,
                        grading_criteria=grading_criteria,
                        acceptable_variants=acceptable_variants,
                        numeric_tol=numeric_tol if kind == "open_numeric" else None,
                    )
                    eval_method = "judge"
                    notes       = f"Final via consolidation; Judge once; kind={kind}. {jnotes}"
                    final_score = judge_score_percent

                # ── Write output row ──────────────────────────────────────────
                output = BenchmarkOutput(
                    run_id               = run_id,
                    task_id              = task_id,
                    model_name           = current_model,
                    model_answer_1       = trial_answers[0] if len(trial_answers) > 0 else None,
                    model_confidence_1   = trial_confs[0]   if len(trial_confs) > 0 else None,
                    model_answer_2       = trial_answers[1] if len(trial_answers) > 1 else None,
                    model_confidence_2   = trial_confs[1]   if len(trial_confs) > 1 else None,
                    model_answer_3       = trial_answers[2] if len(trial_answers) > 2 else None,
                    model_confidence_3   = trial_confs[2]   if len(trial_confs) > 2 else None,
                    final_answer         = final_answer,
                    avg_model_confidence = avg_conf,
                    score_percent_sc_mc  = sc_mc_score_percent,
                    judge_score_percent  = judge_score_percent,
                    judge_confidence     = judge_conf,
                    final_score_percent  = final_score,
                    evaluation_method    = eval_method,
                    token_input          = token_input,
                    token_output         = token_output,
                    judge_token_input    = judge_tok_in  if eval_method == "judge" else None,
                    judge_token_output   = judge_tok_out if eval_method == "judge" else None,
                    token_reasoning      = token_reasoning,
                    evaluated_at_utc     = datetime.now(timezone.utc),
                    evaluation_notes     = notes,
                )
                thread_db.add(output)
                thread_db.commit()

                score_str = f"{final_score:.1f}%" if final_score is not None else "N/A"
                logger.info(f"[PIPELINE] [{current_model}] Done. Score: {score_str}")
                return current_model

            except InsufficientBalanceError:
                thread_db.close()
                raise  # propagate — stops the entire run
            except Exception as e:
                # Judge/consolidation calls are outside the retry loop — treat
                # Insufficient Balance here as fatal (already retried at trial level).
                if 'Insufficient Balance' in str(e):
                    thread_db.close()
                    raise InsufficientBalanceError(
                        f"[{current_model}] Insufficient balance (judge/consolidation call) — stopping run."
                    ) from e
                logger.error(f"[PIPELINE] [{current_model}] Error: {e}", exc_info=True)
                thread_db.rollback()
                return f"ERROR:{current_model}"
            finally:
                thread_db.close()

        # ── 6. Run all models in parallel ─────────────────────────────────────
        # max_workers = number of models so all start immediately.
        # Each worker runs independently — if one model fails the others continue.
        logger.info(
            f"[PIPELINE] Submission {submission_id} — "
            f"running {len(models_to_run)} models in parallel: {models_to_run}"
        )

        failed_models = []
        skipped_models = []
        with ThreadPoolExecutor(max_workers=len(models_to_run)) as executor:
            futures = {
                executor.submit(run_single_model, model): model
                for model in models_to_run
            }

            for future in as_completed(futures):
                try:
                    result = future.result()
                except InsufficientBalanceError:
                    for f in futures:
                        f.cancel()
                    raise
                if result.startswith("ERROR:"):
                    failed_models.append(result.replace("ERROR:", ""))
                    logger.warning(f"[PIPELINE] Model failed: {result}")
                elif result.startswith("SKIP:"):
                    skipped_models.append(result.replace("SKIP:", ""))
                    logger.warning(f"[PIPELINE] Model skipped (not found): {result}")

        # ── 7. Mark done only when every model produced output ────────────────
        submission = db.query(Submission).filter_by(id=submission_id).first()
        submission.completed_at = datetime.now(timezone.utc)

        if failed_models or skipped_models:
            submission.status = "error"
            db.commit()
            raise IncompleteRunError(
                f"Submission {submission_id} incomplete — "
                f"failed: {failed_models}, skipped: {skipped_models}"
            )

        submission.status = "done"
        db.commit()
        logger.info(f"[PIPELINE] Submission {submission_id} — all models complete.")
        return "done"

    except (InsufficientBalanceError, IncompleteRunError):
        raise  # propagate — do not swallow

    except Exception as e:
        logger.error(f"[PIPELINE] Submission {submission_id} — fatal error: {e}", exc_info=True)
        try:
            sub = db.query(Submission).filter_by(id=submission_id).first()
            if sub:
                sub.status       = "error"
                sub.completed_at = datetime.now(timezone.utc)
                db.commit()
        except Exception:
            pass
        return "error"

    finally:
        if close_db:
            db.close()
