"""MCP server exposing generate_slide_image.

Run standalone:  python -m carousel.tools.image_server
The agent talks to it through MCP, so the backend can be swapped (IMAGE_BACKEND env var)
without touching agent code.
"""
from __future__ import annotations

import base64
import hashlib
import os
import uuid
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("slide-image-server")

SIZE = 1080  # square Instagram slide


def _placeholder(prompt: str, style_reference: str, out: Path) -> None:
    """Offline backend: deterministic gradient so the pipeline runs without an image API."""
    from PIL import Image, ImageDraw

    h = hashlib.sha256(prompt.encode()).digest()
    c1 = (h[0] // 2, h[1] // 2, 60 + h[2] // 2)
    c2 = (120 + h[3] // 2, 80 + h[4] // 2, 120 + h[5] // 2)
    img = Image.new("RGB", (SIZE, SIZE))
    d = ImageDraw.Draw(img)
    for y in range(SIZE):
        t = y / SIZE
        d.line([(0, y), (SIZE, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(c1, c2)))
    img.save(out)


def _openai(prompt: str, style_reference: str, out: Path) -> None:
    from openai import OpenAI

    full = f"{prompt}\n\nShared style (follow exactly): {style_reference}\nNo text in the image."
    result = OpenAI().images.generate(
        model=os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-1"),
        prompt=full,
        size="1024x1024",
        quality=os.environ.get("OPENAI_IMAGE_QUALITY", "medium"),  # low | medium | high
    )
    out.write_bytes(base64.b64decode(result.data[0].b64_json))


BACKENDS = {"placeholder": _placeholder, "openai": _openai}


@mcp.tool()
def generate_slide_image(image_prompt: str, style_reference: str, output_dir: str) -> str:
    """Generate one carousel slide background image and return the saved file path.

    Args:
        image_prompt: Text-to-image prompt for this slide.
        style_reference: Shared style spec applied to every slide in the set.
        output_dir: Directory to save the image into.
    """
    backend = os.environ.get("IMAGE_BACKEND", "placeholder")
    if backend not in BACKENDS:
        raise ValueError(f"Unknown IMAGE_BACKEND {backend!r}; choose from {sorted(BACKENDS)}")
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"slide_{uuid.uuid4().hex[:8]}.png"
    BACKENDS[backend](image_prompt, style_reference, out)
    return str(out)


if __name__ == "__main__":
    mcp.run()  # stdio transport
