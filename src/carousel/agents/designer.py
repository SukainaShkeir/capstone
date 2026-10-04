"""Designer: generate -> check -> (Reflexion retry) -> package."""
from __future__ import annotations

import tempfile
from pydantic import BaseModel

from ..llm import LLM
from ..state import CarouselState, SlideImage
from ..tools.check_slide import check_slide
from ..tools.image_client import ImageGenerator
from ..tools.package import package_carousel

MAX_RETRIES = 2

REVISE_SYSTEM = """You revise a failed text-to-image prompt. Reflect on what went wrong, then
write a corrected prompt that fixes the issues while keeping the shared style, no text in the
image, and clear empty space for later text overlay."""


class Revision(BaseModel):
    reflection: str
    prompt: str


async def run(state: CarouselState, llm: LLM, generator: ImageGenerator,
              out_dir: str, work_dir: str | None = None) -> CarouselState:
    assert state.plan and state.prompts, "earlier agents must run first"
    work = work_dir or tempfile.mkdtemp(prefix="carousel_")
    style = state.style_guide.as_text()
    state.images = []
    for i, (slide, prompt) in enumerate(zip(state.plan.slides, state.prompts), start=1):
        item = SlideImage(index=i, prompt=prompt)
        for attempt in range(MAX_RETRIES + 1):
            item.image_path = await generator.generate(item.prompt, style, work)
            check = check_slide(llm, item.image_path, slide, state.style_guide)
            if check.passed:
                item.passed = True
                break
            item.retry_notes.append(f"attempt {attempt + 1}: " + "; ".join(check.issues or ["failed check"]))
            if attempt == MAX_RETRIES:
                item.flagged = True  # out of retries -> curator decides
                break
            rev = llm.parse(
                REVISE_SYSTEM,
                f"Slide: {slide.headline} - {slide.body}\nStyle guide:\n{style}\n"
                f"Failed prompt: {item.prompt}\nIssues found: {item.retry_notes[-1]}",
                Revision,
            )
            item.prompt = rev.prompt
        state.images.append(item)
    package_carousel(state, out_dir)
    return state
