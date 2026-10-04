from types import SimpleNamespace

import pytest
from pydantic import BaseModel

from carousel.llm import LLM, RefusalError


class Out(BaseModel):
    x: int


class FakeModels:
    def __init__(self, resp):
        self.resp, self.kwargs = resp, None

    def generate_content(self, **kw):
        self.kwargs = kw
        return self.resp


def make(resp):
    models = FakeModels(resp)
    return LLM(model="m", client=SimpleNamespace(models=models)), models


def test_parse_returns_model_and_sends_schema():
    llm, models = make(SimpleNamespace(prompt_feedback=None, parsed=Out(x=1), candidates=[]))
    assert llm.parse("sys", "hi", Out) == Out(x=1)
    cfg = models.kwargs["config"]
    assert cfg.response_schema is Out and cfg.system_instruction == "sys"


def test_parse_validates_dict_and_rejects_empty_or_blocked():
    llm, _ = make(SimpleNamespace(prompt_feedback=None, parsed={"x": 2}, candidates=[]))
    assert llm.parse("s", "u", Out).x == 2
    llm, _ = make(SimpleNamespace(prompt_feedback=None, parsed=None, candidates=[]))
    with pytest.raises(RuntimeError):
        llm.parse("s", "u", Out)
    blocked = SimpleNamespace(block_reason="SAFETY")
    llm, _ = make(SimpleNamespace(prompt_feedback=blocked, parsed=None, candidates=[]))
    with pytest.raises(RefusalError):
        llm.parse("s", "u", Out)
