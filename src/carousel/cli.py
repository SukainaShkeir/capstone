from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from .pipeline import load_style, run_pipeline


def read_transcript(path: str | Path) -> str:
    """Read a transcript regardless of how the editor saved it (Windows defaults vary)."""
    data = Path(path).read_bytes()
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):  # UTF-16 (e.g. PowerShell redirect)
        return data.decode("utf-16")
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return data.decode("cp1252", errors="replace")


def check_keys() -> None:
    """Fail early with a plain-language message instead of a deep traceback."""
    import os

    from dotenv import find_dotenv

    if not (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")):
        env = find_dotenv(usecwd=True)
        where = f"Found .env at {env}, but" if env else f"No .env file found in {Path.cwd()}, and"
        raise SystemExit(
            f"{where} GEMINI_API_KEY is empty.\n"
            "Create a file named exactly .env (not .env.txt) in this folder containing:\n"
            "GEMINI_API_KEY=your-key-here\n"
            "(no quotes, no spaces around =)"
        )
    if os.environ.get("IMAGE_BACKEND") == "openai" and not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("IMAGE_BACKEND=openai but OPENAI_API_KEY is empty. "
                         "Add the key to .env, or set IMAGE_BACKEND=placeholder.")


def main() -> None:
    p = argparse.ArgumentParser(description="Turn a video transcript into an Instagram carousel package.")
    p.add_argument("transcript", help="path to a transcript text file")
    p.add_argument("-o", "--out", default="output", help="output directory")
    p.add_argument("--style", help="style guide JSON (default: style_guide.json)")
    p.add_argument("--max-slides", type=int, default=8)
    a = p.parse_args()
    check_keys()
    state = asyncio.run(run_pipeline(
        read_transcript(a.transcript), a.out, load_style(a.style), a.max_slides))
    flagged = [i.index for i in state.images if i.flagged]
    print(f"Wrote {len(state.images)} slides + caption to {state.output_dir}")
    if flagged:
        print(f"Flagged for curator review: slides {flagged}")


if __name__ == "__main__":
    main()
