"""Prompt Writer: slide texts + mood -> one image prompt per slide."""
from __future__ import annotations

from pydantic import BaseModel

from ..llm import LLM
from ..state import CarouselState

SYSTEM = """You are the Prompt Writer. You write text-to-image prompts for Instagram carousel
backgrounds. Every prompt must: share ONE visual style and palette across the whole set, depict
the slide's idea visually, contain NO text, letters, numbers or logos in the image, and leave
clear empty space (e.g. the upper or lower third) where the curator will add text later.
Format: square 1:1."""


class Prompts(BaseModel):
    prompts: list[str]


def run(state: CarouselState, llm: LLM) -> CarouselState:
    assert state.plan, "Content Writer must run first"
    slides = "\n".join(
        f"{i + 1}. {s.headline} - {s.body}" for i, s in enumerate(state.plan.slides)
    )
    out = llm.parse(
        SYSTEM,
        f"Style guide:\n{state.style_guide.as_text()}\n\nMood: {state.plan.mood}\n\n"
        f"Slides:\n{slides}\n\nWrite exactly {len(state.plan.slides)} prompts, in slide order.",
        Prompts,
    )
    if len(out.prompts) != len(state.plan.slides):
        raise ValueError(
            f"Expected {len(state.plan.slides)} prompts, got {len(out.prompts)}"
        )
    state.prompts = out.prompts
    return state
