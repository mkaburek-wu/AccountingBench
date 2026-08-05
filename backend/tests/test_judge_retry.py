"""
Judge-call resilience tests (backend/processing/pipeline.py).

The judge used to be the single least resilient call in the pipeline: no retry
loop, no transient classification, and `max_retries=0` on the client. A single
upstream blip discarded an entire model run *after* all three trials had
already succeeded and been paid for. Real occurrence, 2026-08-05 11:23:21 —
four models failed within 37s on the same gateway fault:

    Error code: 500 - {'error': {'message': 'APIConnectionError:
    AzureException APIConnectionError - Connection error.', ...}}

Retrying the judge cannot bias the benchmark the way retrying a trial would:
by the time the judge runs the model's answer is fixed and stored, so a retry
only re-asks the grader about unchanged input.

No network access — the OpenAI client is replaced with a fake.
"""

import pytest

from backend.processing import pipeline as P


CORTECS_500 = (
    "Error code: 500 - {'error': {'message': 'APIConnectionError: "
    "AzureException APIConnectionError - Connection error.', 'type': None, "
    "'param': None, 'code': '500'}}"
)


# ─────────────────────────────────────────────────────────────────────────────
# _is_transient_error
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("message", [
    CORTECS_500,
    "Error code: 429 - rate limit exceeded",
    "Error code: 502 - Bad Gateway",
    "Error code: 503 - Service Unavailable",
    "Request timed out.",
    "The read operation timed out",
    "ConnectionError",
    "RemoteDisconnected",
    "Connection reset by peer",
])
def test_transient_errors_are_recognised(message):
    """The gateway reports its own upstream failures inside the message body,
    so classification matches on the string rather than a status attribute.
    """
    assert P._is_transient_error(RuntimeError(message)) is True


@pytest.mark.parametrize("message", [
    "Error code: 404 - DeploymentNotFound",
    "Error code: 400 - Unsupported value: 'temperature'",
    "Error code: 401 - AuthenticationError",
    "some unrelated failure",
])
def test_permanent_errors_are_not_retried(message):
    """Retrying these only wastes a call — the deployment name, request body or
    key is wrong and will be wrong again.
    """
    assert P._is_transient_error(RuntimeError(message)) is False


# ─────────────────────────────────────────────────────────────────────────────
# call_judge retry behaviour
# ─────────────────────────────────────────────────────────────────────────────

class _FakeCompletions:
    def __init__(self, owner):
        self._owner = owner

    def create(self, **kwargs):
        self._owner.calls += 1
        if self._owner.calls <= len(self._owner.failures):
            raise RuntimeError(self._owner.failures[self._owner.calls - 1])
        return _FakeResponse(self._owner.reply)


class _FakeResponse:
    def __init__(self, content):
        self.choices = [type("C", (), {"message": type("M", (), {"content": content})()})()]
        self.usage = None


class _FakeClient:
    """Records how often it was called and which failures to raise first."""

    def __init__(self, failures=(), reply='{"score_percent": 100, "confidence": 0.9, "notes": "ok"}'):
        self.failures = list(failures)
        self.reply = reply
        self.calls = 0
        self.with_options_kwargs = None
        self.chat = type("Chat", (), {"completions": _FakeCompletions(self)})()

    def with_options(self, **kwargs):
        self.with_options_kwargs = kwargs
        return self


@pytest.fixture
def judge_client(monkeypatch):
    """Install a fake judge client and make retry sleeps instant."""
    holder = {}

    def _install(**kwargs):
        client = _FakeClient(**kwargs)
        monkeypatch.setattr(P, "_get_client_for_model", lambda m: (client, "openai_v1"))
        monkeypatch.setattr(P, "_is_responses_only_model", lambda m: False)
        monkeypatch.setattr(P.time, "sleep", lambda s: None)
        monkeypatch.setattr(P, "log_raw_response", lambda *a, **k: None)
        holder["client"] = client
        return client

    _install.holder = holder
    return _install


def _judge():
    return P.call_judge("Frage?", "Antwort", "GOLD", context={"task_id": 1, "model": "m"})


def test_judge_retries_a_transient_failure_and_succeeds(judge_client):
    """The 2026-08-05 case: one gateway 500, then a healthy response. This used
    to abort the whole model run; it must now simply recover.
    """
    client = judge_client(failures=[CORTECS_500])
    score, conf, notes, _, _ = _judge()
    assert client.calls == 2
    assert score == 100.0
    assert notes == "ok"


def test_judge_retries_up_to_the_attempt_limit(judge_client):
    client = judge_client(failures=[CORTECS_500, CORTECS_500])
    score, _, _, _, _ = _judge()
    assert client.calls == P.JUDGE_MAX_ATTEMPTS == 3
    assert score == 100.0


def test_judge_gives_up_after_the_attempt_limit(judge_client):
    """Persistent outage must still surface as an error rather than a silent 0
    — a fabricated 0 would be indistinguishable from a real judged failure.
    """
    client = judge_client(failures=[CORTECS_500] * 5)
    with pytest.raises(RuntimeError):
        _judge()
    assert client.calls == P.JUDGE_MAX_ATTEMPTS


def test_judge_does_not_retry_a_permanent_error(judge_client):
    client = judge_client(failures=["Error code: 400 - Unsupported value: 'temperature'"])
    with pytest.raises(RuntimeError):
        _judge()
    assert client.calls == 1


def test_judge_uses_a_client_copy_not_the_shared_cached_one(judge_client):
    """JUDGE_MODEL and the benchmarked 'gpt-5-mini' share a CLIENT_CACHE entry.

    SDK-level retries are invisible to the trial-integrity check, so raising
    max_retries on the *shared* client would let a benchmark trial be retried
    without trial_needed_retry ever being set — silently violating the rule
    that scores come from clean, uninterrupted runs.
    """
    client = judge_client()
    _judge()
    assert client.with_options_kwargs == {"max_retries": P.JUDGE_SDK_RETRIES}


def test_unparseable_judge_reply_still_scores_zero_without_retrying(judge_client):
    """A reply that arrives but isn't JSON is not a transport fault — retrying
    would just burn calls. It keeps the documented judge_parse_error path.
    """
    client = judge_client(reply="not json at all")
    score, conf, notes, _, _ = _judge()
    assert client.calls == 1
    assert score == 0.0
    assert notes == "judge_parse_error"
