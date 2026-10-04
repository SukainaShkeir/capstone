from types import SimpleNamespace

import pytest
from pydantic import BaseModel

from carousel.llm import LLM, RefusalError


class Out(BaseModel):
    x: int


class FakeResponses:
    def __init__(self, resp):
        self.resp, self.kwargs = resp, None

    def parse(self, **kw):
        self.kwargs = kw
        return self.resp


def make(resp, **kw):
    responses = FakeResponses(resp)
    return LLM(model="m", client=SimpleNamespace(responses=responses), **kw), responses


def ok(parsed):
    return SimpleNamespace(output=[], output_parsed=parsed, status="completed", incomplete_details=None)


def test_parse_returns_model_and_sends_schema():
    llm, r = make(ok(Out(x=1)))
    assert llm.parse("sys", "hi", Out) == Out(x=1)
    assert r.kwargs["text_format"] is Out and r.kwargs["instructions"] == "sys"
    assert "reasoning" not in r.kwargs


def test_reasoning_effort_is_passed_when_set():
    llm, r = make(ok(Out(x=1)), reasoning_effort="low")
    llm.parse("s", "u", Out)
    assert r.kwargs["reasoning"] == {"effort": "low"}


def test_empty_and_refusal_raise():
    llm, _ = make(ok(None))
    with pytest.raises(RuntimeError):
        llm.parse("s", "u", Out)
    refusal = SimpleNamespace(type="message", content=[SimpleNamespace(type="refusal", refusal="no")])
    llm, _ = make(SimpleNamespace(output=[refusal], output_parsed=None, status="completed",
                                  incomplete_details=None))
    with pytest.raises(RefusalError):
        llm.parse("s", "u", Out)


def test_image_is_sent_as_input_image(tmp_path):
    img = tmp_path / "a.png"
    img.write_bytes(b"\x89PNG")
    llm, r = make(ok(Out(x=1)))
    llm.parse_with_image("s", "look", img, Out)
    parts = r.kwargs["input"][0]["content"]
    assert parts[0]["type"] == "input_image" and parts[0]["image_url"].startswith("data:image/png;base64,")
    assert parts[1] == {"type": "input_text", "text": "look"}


def test_schemas_are_valid_for_openai_strict_mode():
    from openai.lib._pydantic import to_strict_json_schema

    from carousel.agents.content_writer import Outlines
    from carousel.agents.designer import Revision
    from carousel.agents.prompt_writer import Prompts
    from carousel.state import SlidePlan
    from carousel.tools.check_slide import SlideCheck

    for s in (Outlines, Prompts, Revision, SlidePlan, SlideCheck):
        to_strict_json_schema(s)
