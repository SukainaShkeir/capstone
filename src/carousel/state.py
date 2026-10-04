"""Shared short-term memory: grows at each agent handoff."""
from __future__ import annotations

from pydantic import BaseModel, Field


class StyleGuide(BaseModel):
    brand: str
    palette: list[str]
    visual_style: str
    fonts: str
    tone: str

    def as_text(self) -> str:
        return (
            f"Brand: {self.brand}\nPalette: {', '.join(self.palette)}\n"
            f"Visual style: {self.visual_style}\nFonts (applied later): {self.fonts}\nTone: {self.tone}"
        )


class SlideText(BaseModel):
    headline: str
    body: str


class SlidePlan(BaseModel):
    """Content Writer output (also its structured-output schema)."""

    slides: list[SlideText]
    caption: str
    mood: str


class SlideImage(BaseModel):
    index: int
    prompt: str
    image_path: str | None = None
    passed: bool = False
    flagged: bool = False  # still failing after retries -> curator must look
    retry_notes: list[str] = Field(default_factory=list)


class CarouselState(BaseModel):
    transcript: str
    style_guide: StyleGuide
    max_slides: int = 8
    plan: SlidePlan | None = None
    prompts: list[str] = Field(default_factory=list)
    images: list[SlideImage] = Field(default_factory=list)
    output_dir: str | None = None
