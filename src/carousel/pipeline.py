"""Sequential hand-off workflow: Content Writer -> Prompt Writer -> Designer."""
from __future__ import annotations

import json
from pathlib import Path

from .agents import content_writer, designer, prompt_writer
from .llm import LLM
from .state import CarouselState, StyleGuide
from .tools.image_client import ImageGenerator, McpImageGenerator

DEFAULT_STYLE = Path(__file__).resolve().parents[2] / "style_guide.json"


def load_style(path: str | Path | None = None) -> StyleGuide:
    return StyleGuide(**json.loads(Path(path or DEFAULT_STYLE).read_text(encoding="utf-8")))


async def run_pipeline(transcript: str, out_dir: str, style: StyleGuide | None = None,
                       max_slides: int = 8, llm: LLM | None = None,
                       generator: ImageGenerator | None = None) -> CarouselState:
    llm = llm or LLM()
    generator = generator or McpImageGenerator()
    state = CarouselState(transcript=transcript, style_guide=style or load_style(),
                          max_slides=max_slides)
    state = content_writer.run(state, llm)
    state = prompt_writer.run(state, llm)
    return await designer.run(state, llm, generator, out_dir)
