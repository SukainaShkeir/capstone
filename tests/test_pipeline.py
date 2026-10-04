import asyncio
import json

from carousel.agents.content_writer import Outline, Outlines
from carousel.agents.designer import Revision
from carousel.agents.prompt_writer import Prompts
from carousel.pipeline import load_style, run_pipeline
from carousel.state import SlidePlan, SlideText
from carousel.tools.check_slide import SlideCheck
from carousel.tools.image_client import McpImageGenerator


class FakeLLM:
    """Scripted stand-in for the LLM wrapper; first image check fails once."""

    def __init__(self, fail_first_check=True, always_fail=False):
        self.checks = 0
        self.fail_first = fail_first_check
        self.always_fail = always_fail

    def parse(self, system, user, schema, **_):
        if schema is Outlines:
            return Outlines(core_message="m", candidates=[
                Outline(approach="a", slide_titles=["x"], strengths="s", weaknesses="w")])
        if schema is SlidePlan:  # returns 12 slides to exercise the limit
            return SlidePlan(slides=[SlideText(headline=f"H{i}", body="b") for i in range(12)],
                             caption="cap #tag", mood="calm")
        if schema is Prompts:
            n = user.count("\n") and sum(1 for l in user.splitlines() if l[:1].isdigit() and ". " in l[:4])
            return Prompts(prompts=[f"p{i}" for i in range(n)])
        if schema is Revision:
            return Revision(reflection="r", prompt="revised")
        raise AssertionError(schema)

    def parse_with_image(self, system, text, image_path, schema):
        self.checks += 1
        bad = self.always_fail or (self.fail_first and self.checks == 1)
        return SlideCheck(on_style=True, contains_text=bad, matches_slide=True,
                          has_text_space=True, issues=["text visible"] if bad else [])


def test_pipeline_end_to_end(tmp_path):
    state = asyncio.run(run_pipeline("transcript", str(tmp_path), load_style(), max_slides=3,
                                     llm=FakeLLM(), generator=McpImageGenerator("placeholder")))
    assert len(state.images) == 3  # slide limit enforced
    assert state.images[0].retry_notes and state.images[0].passed  # Reflexion retry recovered
    assert state.images[0].prompt == "revised"
    data = json.loads((tmp_path / "carousel.json").read_text())
    assert len(data["slides"]) == 3 and (tmp_path / "slide_01.png").exists()
    assert (tmp_path / "caption.txt").read_text() == "cap #tag"


def test_flagged_after_two_retries(tmp_path):
    state = asyncio.run(run_pipeline("t", str(tmp_path), max_slides=1,
                                     llm=FakeLLM(always_fail=True),
                                     generator=McpImageGenerator("placeholder")))
    img = state.images[0]
    assert img.flagged and not img.passed and len(img.retry_notes) == 3


def test_read_transcript_encodings(tmp_path):
    from carousel.cli import read_transcript

    text = "It’s a “test” — café \U0001F600"
    for name, enc in [("a", "utf-8"), ("b", "utf-8-sig"), ("c", "utf-16")]:
        f = tmp_path / name
        f.write_bytes(text.encode(enc))
        assert read_transcript(f) == text
    f = tmp_path / "d"
    f.write_bytes("café".encode("cp1252"))
    assert read_transcript(f) == "café"


def test_env_loader_handles_bom_and_utf16(tmp_path):
    import os
    import subprocess
    import sys

    for name, raw in [("bom", b"\xef\xbb\xbfOPENAI_API_KEY=abc\r\nIMAGE_BACKEND=placeholder\r\n"),
                      ("u16", "OPENAI_API_KEY=abc\r\n".encode("utf-16"))]:
        d = tmp_path / name
        d.mkdir()
        (d / ".env").write_bytes(raw)
        env = {k: v for k, v in os.environ.items() if k != "OPENAI_API_KEY"}
        out = subprocess.run([sys.executable, "-c",
                              "import os, carousel; print(os.environ.get('OPENAI_API_KEY'), carousel.ENV_NAMES)"],
                             cwd=d, env=env, capture_output=True, text=True).stdout
        assert out.startswith("abc"), (name, out)
