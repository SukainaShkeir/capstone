"""check_slide: vision review (Gemini) of one generated image against its slide + style guide."""
from __future__ import annotations

from pydantic import BaseModel

from ..llm import LLM
from ..state import SlideText, StyleGuide

SYSTEM = "You are a strict art director reviewing an Instagram carousel background image."


class SlideCheck(BaseModel):
    on_style: bool
    contains_text: bool  # any letters/numbers/logos visible in the image
    matches_slide: bool
    has_text_space: bool
    issues: list[str]

    @property
    def passed(self) -> bool:
        return self.on_style and not self.contains_text and self.matches_slide and self.has_text_space


def check_slide(llm: LLM, image_path: str, slide: SlideText, style: StyleGuide) -> SlideCheck:
    return llm.parse_with_image(
        SYSTEM,
        f"Style guide:\n{style.as_text()}\n\nThis image is the background for a slide:\n"
        f"Headline: {slide.headline}\nBody: {slide.body}\n\n"
        "Judge: on_style (matches the style guide), contains_text (any visible text/logos - must be "
        "false), matches_slide (visually supports the slide's idea), has_text_space (clear empty "
        "area for overlaying text). List concrete issues; empty list if none.",
        image_path,
        SlideCheck,
    )
