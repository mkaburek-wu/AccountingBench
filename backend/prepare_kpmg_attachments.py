"""Build the model-facing attachment PDFs for the KPMG IFRS 10 control case.

The pipeline truncates every attached document to ATTACHMENTS_MAX_CHARS (12 000)
keeping only the first 75 % and last 20 % (processing/pipeline.py::_truncate_text).
Both source documents are far over that limit, and the clauses the case actually
turns on sit in the discarded middle:

  * Gesellschaftsvertrag (31 500 chars) -> would lose SS 6 (Letztentscheidungsrecht),
    SS 8 (quorum) and SS 9 (majorities, EUR 1 = 1 vote)
  * Anlagen 1-3 (27 997 chars)          -> would lose Anlage 3 SS 3 Abs. 1 Nr. 3
    "die Festlegung des Jahresbudgets"

So each source is split into whole units that individually stay under the cap.
Nothing is truncated and no clause is cut in half.

Two deliberate differences in how the two sources are handled:

  * The Gesellschaftsvertrag is a .docx. A non-PDF attachment reaches the model as
    ZIP garbage (pipeline.py:592), so it must be rendered to a text-layer PDF. Word
    COM automation is not available here, so the text is re-rendered with PyMuPDF.
    Word's automatic list numbering lives in the numbering definition rather than in
    the paragraph text, so it is reconstructed from numPr/ilvl and written out as
    "(1)", "(2)", ... -- without it the model could not cite "SS 6 Abs. 8" and the
    gold answers' clause references would be ungradeable.
  * The Anlagen are already a PDF whose tables carry meaning in their layout, so
    they are split with insert_pdf, which copies the page objects and preserves the
    original OCR text layer verbatim. They are never re-rendered.

Run from the project root:

    python -m backend.prepare_kpmg_attachments

Writes to backend/uploads/Use_cases/KPMG/attachments/ and is safe to re-run.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import fitz
from docx import Document

SECTION = chr(167)  # paragraph sign, kept out of the source literal for encoding safety

BASE = Path(__file__).resolve().parent / "uploads" / "Use_cases" / "KPMG"
OUT_DIR = BASE / "attachments"
CONTRACT_DOCX = BASE / "Gesellschaftsvertrag Beispiel 1.docx"
ANNEX_PDF = BASE / "K4414-2025_geschwärzt_OCR-2.pdf"

# Must stay in step with ATTACHMENTS_MAX_CHARS in processing/pipeline.py. A margin is
# kept below the real cap so small rendering differences can never push a part over.
MAX_CHARS = 12_000
SAFE_CHARS = 11_600

# Contract parts, as (filename stem, first section, last section). The groupings keep
# every section whole and were chosen from the measured section lengths.
CONTRACT_PARTS = [
    ("GV_Teil1_Par1-7", 1, 7),
    ("GV_Teil2_Par8-11", 8, 11),
    ("GV_Teil3_Par12-18", 12, 18),
    ("GV_Teil4_Par19-20", 19, 20),
]

# Annex parts, as (filename stem, first page, last page), 1-based inclusive.
ANNEX_PARTS = [
    ("Anlage1_Genehmigungscheckliste_Teil1", 1, 3),
    ("Anlage1_Genehmigungscheckliste_Teil2", 4, 5),
    ("Anlage2_Freigaberegelung", 6, 9),
    ("Anlage3_Geschaeftsordnung", 10, 14),
]

# Page geometry for the rendered contract PDFs.
PAGE_W, PAGE_H = fitz.paper_size("a4")
MARGIN = 56
FONT = "helv"
FONT_SIZE = 10
LINE_H = 13.5

# Intra-word hyphens left behind by whatever conversion produced the anonymised
# .docx ("be-rechtigt", "Kapitalver-lustkonten"). They are joined so that models are
# not penalised for noise we introduced; every join is logged for audit. The pattern
# only matches lowercase-hyphen-lowercase with no surrounding space, so legitimate
# German compounds ("Gewinn- und Verlustverteilung", "Soll-Ist-Vergleich") are safe.
DEHYPHENATE = re.compile(r"([a-zäöüß])-([a-zäöüß])")

# The base-14 Helvetica used for rendering is Latin-1 only, so typographic
# punctuation outside that range would be dropped silently. The contract uses the
# German opening quote; the rest are mapped defensively.
CHAR_FALLBACKS = {
    "„": '"', "“": '"', "”": '"', "‚": "'",
    "‘": "'", "’": "'", "–": "-", "—": "-",
    "…": "...", " ": " ", "‑": "-",
}

# Unnumbered paragraphs are classified by their Word indent: the deeper ones are
# sub-items of the preceding Absatz (e.g. the three matters subject to Max Huber
# Rail's Letztentscheidungsrecht in SS 6 Abs. 8), the shallower ones are
# continuation lines of that Absatz.
SUBITEM_INDENT_PT = 40.0


def _normalise(text: str) -> str:
    for source, replacement in CHAR_FALLBACKS.items():
        text = text.replace(source, replacement)
    return text


def _left_indent_pt(paragraph) -> float:
    indent = paragraph.paragraph_format.left_indent
    return float(indent.pt) if indent is not None else 0.0


def _list_level(paragraph) -> int | None:
    """Word list level of a paragraph, or None if it is not a list item."""
    p_pr = paragraph._p.pPr
    if p_pr is None or p_pr.numPr is None:
        return None
    ilvl = p_pr.numPr.ilvl
    return ilvl.val if ilvl is not None else 0


def _is_section_heading(text: str) -> int | None:
    """Return the section number if the paragraph is a bare section heading."""
    stripped = text.strip()
    if not stripped.startswith(SECTION) or len(stripped) > 12:
        return None
    digits = re.search(r"\d+", stripped)
    return int(digits.group()) if digits else None


def extract_contract_sections() -> dict[int, list[str]]:
    """Read the contract and return {section number: [rendered lines]}.

    List numbering is reconstructed from numPr/ilvl: level 0 items become "(n)"
    Absaetze, level 1 items become indented "n." entries that restart inside each
    Absatz -- matching how Word displays the document and how the contract refers to
    itself ("Einlagen gemaess SS 3 Abs. 2").
    """
    document = Document(CONTRACT_DOCX)
    sections: dict[int, list[str]] = {}
    joins: list[tuple[str, str]] = []

    current: int | None = None
    abs_no = 0
    nr_no = 0

    for paragraph in document.paragraphs:
        text = " ".join(paragraph.text.split())
        if not text:
            continue

        heading = _is_section_heading(text)
        if heading is not None:
            current = heading
            sections[current] = [f"{SECTION} {current}"]
            abs_no = 0
            nr_no = 0
            continue

        if current is None:
            continue  # title block before the first section

        cleaned = DEHYPHENATE.sub(r"\1\2", text)
        if cleaned != text:
            joins.append((text, cleaned))
        cleaned = _normalise(cleaned)

        level = _list_level(paragraph)
        if level == 0:
            abs_no += 1
            nr_no = 0
            sections[current].append(f"({abs_no}) {cleaned}")
        elif level == 1:
            nr_no += 1
            sections[current].append(f"      {nr_no}. {cleaned}")
        elif _left_indent_pt(paragraph) >= SUBITEM_INDENT_PT:
            # Unnumbered sub-item of the current Absatz - keep it visibly subordinate.
            sections[current].append(f"      - {cleaned}")
        else:
            # Section subtitle or a continuation line of the current Absatz.
            sections[current].append(cleaned)

    if joins:
        log = OUT_DIR / "dehyphenation_log.txt"
        log.write_text(
            "Intra-word hyphens joined while rendering the Gesellschaftsvertrag.\n"
            f"{len(joins)} paragraph(s) affected.\n\n"
            + "\n\n".join(f"- before: {b}\n  after : {a}" for b, a in joins),
            encoding="utf-8",
        )
        print(f"  de-hyphenated {len(joins)} paragraph(s) -> {log.name}")

    return sections


def _wrap(text: str, width: float) -> list[str]:
    """Greedy wrap honouring the leading indent of continuation lines."""
    indent = len(text) - len(text.lstrip())
    prefix = " " * indent
    words = text.split()
    lines: list[str] = []
    line = ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if fitz.get_text_length(prefix + candidate, FONT, FONT_SIZE) <= width and line:
            line = candidate
        elif not line:
            line = word
        else:
            lines.append(prefix + line)
            line = word
    if line:
        lines.append(prefix + line)
    return lines or [""]


def render_text_pdf(lines: list[str], out_path: Path, title: str) -> None:
    """Render wrapped lines to a paginated text-layer PDF."""
    width = PAGE_W - 2 * MARGIN
    wrapped: list[str] = []
    for line in lines:
        if not line.strip():
            wrapped.append("")
            continue
        wrapped.extend(_wrap(line, width))
        wrapped.append("")

    doc = fitz.open()
    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    y = MARGIN
    page.insert_text((MARGIN, y), title, fontname=FONT, fontsize=FONT_SIZE + 1)
    y += LINE_H * 2

    for line in wrapped:
        if y > PAGE_H - MARGIN:
            page = doc.new_page(width=PAGE_W, height=PAGE_H)
            y = MARGIN
        if line:
            page.insert_text((MARGIN, y), line, fontname=FONT, fontsize=FONT_SIZE)
        y += LINE_H

    doc.save(out_path, deflate=True)
    doc.close()


def build_contract_parts(sections: dict[int, list[str]]) -> list[Path]:
    written = []
    for stem, first, last in CONTRACT_PARTS:
        lines: list[str] = [
            "Gesellschaftsvertrag der Paul Schwarz GmbH & Co. KG",
            f"(Auszug: {SECTION}{SECTION} {first} bis {last} von 20)",
            "",
        ]
        for number in range(first, last + 1):
            if number not in sections:
                continue
            lines.extend(sections[number])
            lines.append("")
        out_path = OUT_DIR / f"{stem}.pdf"
        render_text_pdf(
            lines,
            out_path,
            f"Gesellschaftsvertrag Paul Schwarz GmbH & Co. KG "
            f"- {SECTION}{SECTION} {first}-{last}",
        )
        written.append(out_path)
    return written


def build_annex_parts() -> list[Path]:
    source = fitz.open(ANNEX_PDF)
    written = []
    for stem, first, last in ANNEX_PARTS:
        part = fitz.open()
        part.insert_pdf(source, from_page=first - 1, to_page=last - 1)
        out_path = OUT_DIR / f"{stem}.pdf"
        part.save(out_path, deflate=True)
        part.close()
        written.append(out_path)
    source.close()
    return written


# Every link in the control analysis must survive the split. If any of these is
# missing the case is not answerable from the attachments alone.
DECISIVE_STRINGS = [
    "Letztentscheidungsrecht",                     # SS 6 Abs. 8
    "Investitionsentscheidungen innerhalb der bestehenden Budgetplanung",
    "Genehmigungsprozess",                          # SS 6 Abs. 5, makes Anlage 1 binding
    "625.000,00 EUR",                               # SS 3 Abs. 2 Nr. 1, Max Huber Rail's capital
    "208.334,00 EUR",                               # SS 3 Abs. 2 Nr. 2
    "Je 1,- EUR des Kapitalkontos",                 # SS 9 Abs. 4, one euro one vote
    "Mehrheit von 2/3 der Stimmen der anwesenden",  # SS 9 Abs. 2
    "Zustimmung zu zustimmungspflichtigen",         # SS 9 Abs. 2 Nr. 3
    "zweite Gesellschafterversammlung",             # SS 8 Abs. 5, quorum-free second meeting
    "Festlegung des Jahresbudgets",                 # Anlage 3 SS 3 Abs. 1 Nr. 3
]

# Nothing from the ground-truth sources may ever appear in a model-facing document.
CONTAMINATION_STRINGS = ["mklaus@kpmg.at", "Kaburek", "Im Ergebnis beherrscht keine Partei"]


def verify(paths: list[Path]) -> list[str]:
    """Check every produced PDF against what the pipeline requires of it."""
    problems: list[str] = []
    corpus_parts = []

    print()
    print(f"{'file':44s} {'pages':>5s} {'chars':>7s}  status")
    print("-" * 74)
    for path in paths:
        name = path.name
        if "," in str(path) or ";" in str(path):
            problems.append(f"{name}: path contains ',' or ';' - would break _split_attached_files")

        with fitz.open(path) as doc:
            text = "\n\n".join(p.get_text() for p in doc).strip()
            pages = doc.page_count
        corpus_parts.append(text)

        status = "ok"
        if not text:
            problems.append(f"{name}: no text layer - pipeline would raise PDF_NO_TEXT")
            status = "NO TEXT LAYER"
        elif len(text) > MAX_CHARS:
            problems.append(f"{name}: {len(text)} chars exceeds ATTACHMENTS_MAX_CHARS={MAX_CHARS}")
            status = "OVER CAP"
        elif len(text) > SAFE_CHARS:
            status = "ok (near cap)"

        print(f"{name:44s} {pages:5d} {len(text):7d}  {status}")

    corpus = "\n".join(corpus_parts)

    print()
    print("decisive content present in the split corpus:")
    for needle in DECISIVE_STRINGS:
        found = needle in corpus
        print(f"  [{'x' if found else ' '}] {needle}")
        if not found:
            problems.append(f"decisive string missing from the attachments: {needle!r}")

    for needle in CONTAMINATION_STRINGS:
        if needle in corpus:
            problems.append(f"CONTAMINATION: ground-truth text {needle!r} leaked into an attachment")

    return problems


def main() -> int:
    for required in (CONTRACT_DOCX, ANNEX_PDF):
        if not required.exists():
            print(f"ERROR: missing source document: {required}")
            return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Extracting Gesellschaftsvertrag ...")
    sections = extract_contract_sections()
    print(f"  {len(sections)} sections found")

    print("Rendering contract parts ...")
    contract_paths = build_contract_parts(sections)

    print("Splitting Anlagen 1-3 ...")
    annex_paths = build_annex_parts()

    paths = contract_paths + annex_paths
    problems = verify(paths)

    print()
    print("attached_files cell value (copy verbatim into the Questions sheet):")
    print()
    print(" | ".join(str(p) for p in paths))
    print()

    if problems:
        print("FAILED:")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    print(f"OK - {len(paths)} attachment PDFs written to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
