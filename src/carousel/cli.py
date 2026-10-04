from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from .pipeline import load_style, run_pipeline


def main() -> None:
    p = argparse.ArgumentParser(description="Turn a video transcript into an Instagram carousel package.")
    p.add_argument("transcript", help="path to a transcript text file")
    p.add_argument("-o", "--out", default="output", help="output directory")
    p.add_argument("--style", help="style guide JSON (default: style_guide.json)")
    p.add_argument("--max-slides", type=int, default=8)
    a = p.parse_args()
    state = asyncio.run(run_pipeline(
        Path(a.transcript).read_text(), a.out, load_style(a.style), a.max_slides))
    flagged = [i.index for i in state.images if i.flagged]
    print(f"Wrote {len(state.images)} slides + caption to {state.output_dir}")
    if flagged:
        print(f"Flagged for curator review: slides {flagged}")


if __name__ == "__main__":
    main()
