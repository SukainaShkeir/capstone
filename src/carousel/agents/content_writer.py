"""Content Writer: transcript -> slide texts, caption, mood (tree-of-thoughts)."""
from __future__ import annotations

from pydantic import BaseModel

from ..llm import LLM
from ..state import CarouselState, SlidePlan

SYSTEM = """You are the Content Writer in a transcript-to-Instagram-carousel team.
Rules: stay strictly faithful to the transcript (no invented facts or quotes), never exceed
the slide limit, and follow the style guide's tone. Slide 1 is a hook, the last slide is a
takeaway or call to action. Headlines are short (<= 8 words); bodies are <= 25 words."""


class Outline(BaseModel):
    approach: str
    slide_titles: list[str]
    strengths: str
    weaknesses: str


class Outlines(BaseModel):
    core_message: str
    candidates: list[Outline]


def run(state: CarouselState, llm: LLM) -> CarouselState:
    context = (
        f"Style guide:\n{state.style_guide.as_text()}\n\nSlide limit: {state.max_slides}\n\n"
        f"Transcript:\n{state.transcript}"
    )
    # Tree-of-thoughts, branch step: propose several distinct slide breakdowns.
    outlines = llm.parse(
        SYSTEM,
        f"{context}\n\nExtract the core message, then propose 3 genuinely different slide "
        f"breakdowns (e.g. problem->solution, numbered tips, story arc). Each must have at most "
        f"{state.max_slides} slides.",
        Outlines,
    )
    options = "\n\n".join(
        f"Option {i + 1} ({o.approach}): {' | '.join(o.slide_titles)}\n"
        f"  + {o.strengths}\n  - {o.weaknesses}"
        for i, o in enumerate(outlines.candidates)
    )
    # Evaluate-and-commit step: pick the best branch and write the final copy.
    plan = llm.parse(
        SYSTEM,
        f"{context}\n\nCore message: {outlines.core_message}\n\nCandidate breakdowns:\n{options}\n\n"
        f"Compare the options, pick the one that tells the story best, and write the final "
        f"slides (headline + body each), an Instagram caption (with a few hashtags), and a short "
        f"'mood' description (colour/atmosphere/feel) for the image set.",
        SlidePlan,
    )
    if not plan.slides:
        raise ValueError("Content Writer returned no slides")
    plan.slides = plan.slides[: state.max_slides]  # enforce the slide limit
    state.plan = plan
    return state
