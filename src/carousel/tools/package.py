"""package_carousel: save images, slide texts and caption together."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from ..state import CarouselState


def package_carousel(state: CarouselState, out_dir: str | Path) -> Path:
    assert state.plan, "no plan to package"
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    slides = []
    for img, text in zip(state.images, state.plan.slides):
        name = f"slide_{img.index:02d}.png"
        if img.image_path:
            shutil.copy(img.image_path, out / name)
        slides.append({
            "slide": img.index,
            "image": name if img.image_path else None,
            "headline": text.headline,
            "body": text.body,
            "flagged_for_curator": img.flagged,
            "retry_notes": img.retry_notes,
        })
    (out / "caption.txt").write_text(state.plan.caption, encoding="utf-8")
    (out / "carousel.json").write_text(json.dumps(
        {"mood": state.plan.mood, "caption": state.plan.caption, "slides": slides}, indent=2), encoding="utf-8")
    state.output_dir = str(out)
    return out
