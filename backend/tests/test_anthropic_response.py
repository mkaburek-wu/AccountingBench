"""
Reading text out of an Anthropic Messages response.

`resp.content` is a list of blocks and the first one is not necessarily the
answer. With extended thinking enabled the model emits a ThinkingBlock first,
which carries `.thinking` and has no `.text` at all. The pipeline used to read
`resp.content[0].text` unconditionally, so every call to a thinking-enabled
model died with:

    AttributeError: 'ThinkingBlock' object has no attribute 'text'

That killed the whole model run — observed on claude-fable-5, 2026-08-12,
where it failed on trial 1 of every task after a successful 200 OK.

No network access — the response objects are stand-ins with the same shape.
"""

import pytest

from backend.processing.pipeline import anthropic_content_text


class Block:
    """Minimal stand-in for an Anthropic content block."""

    def __init__(self, type=None, **kwargs):
        if type is not None:
            self.type = type
        for k, v in kwargs.items():
            setattr(self, k, v)


class Resp:
    def __init__(self, content, stop_reason="end_turn"):
        self.content = content
        self.stop_reason = stop_reason


ANSWER = '{"answer": "A", "confidence": 0.9}'


def test_thinking_block_before_text_does_not_crash():
    """The exact claude-fable-5 failure: ThinkingBlock at index 0."""
    resp = Resp([
        Block("thinking", thinking="Lass mich das durchrechnen …"),
        Block("text", text=ANSWER),
    ])
    text, thinking = anthropic_content_text(resp)
    assert text == ANSWER
    assert thinking == "Lass mich das durchrechnen …"


def test_plain_text_response_still_works():
    """Non-thinking models must be unaffected — this is the common path."""
    text, thinking = anthropic_content_text(Resp([Block("text", text=ANSWER)]))
    assert text == ANSWER
    assert thinking == ""


def test_multiple_text_blocks_are_joined_in_order():
    """A long answer can be split across blocks; dropping any loses the JSON."""
    resp = Resp([
        Block("thinking", thinking="…"),
        Block("text", text='{"answer": "Teil eins'),
        Block("text", text=' und Teil zwei", "confidence": 0.8}'),
    ])
    text, _ = anthropic_content_text(resp)
    assert text == '{"answer": "Teil eins\n und Teil zwei", "confidence": 0.8}'


def test_redacted_thinking_is_recorded_but_not_treated_as_answer():
    resp = Resp([
        Block("redacted_thinking", data="encrypted-blob"),
        Block("text", text=ANSWER),
    ])
    text, thinking = anthropic_content_text(resp)
    assert text == ANSWER
    assert thinking == "[redacted_thinking]"


def test_thinking_only_response_returns_empty_text_without_raising():
    """Happens when the thinking budget consumes max_tokens. Must degrade to an
    empty answer the caller can report, not an AttributeError mid-run.
    """
    resp = Resp([Block("thinking", thinking="…")], stop_reason="max_tokens")
    text, thinking = anthropic_content_text(resp)
    assert text == ""
    assert thinking == "…"


def test_tool_use_block_is_ignored():
    resp = Resp([Block("tool_use", id="x", name="calc", input={}),
                 Block("text", text=ANSWER)])
    text, _ = anthropic_content_text(resp)
    assert text == ANSWER


def test_untyped_block_with_text_is_still_read():
    """Older/pre-typed SDK shapes expose .text with no .type. Taking it beats
    silently returning nothing when it is the only content present.
    """
    text, _ = anthropic_content_text(Resp([Block(text=ANSWER)]))
    assert text == ANSWER


@pytest.mark.parametrize("content", [None, []])
def test_missing_or_empty_content_returns_empty(content):
    text, thinking = anthropic_content_text(Resp(content))
    assert text == ""
    assert thinking == ""
