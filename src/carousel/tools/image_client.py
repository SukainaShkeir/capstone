"""MCP client the Designer uses to call generate_slide_image."""
from __future__ import annotations

import os
import sys
from typing import Protocol

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class ImageGenerator(Protocol):
    async def generate(self, image_prompt: str, style_reference: str, output_dir: str) -> str: ...


class McpImageGenerator:
    """Spawns the image server over stdio and calls the tool for each request."""

    def __init__(self, backend: str | None = None):
        env = dict(os.environ)
        if backend:
            env["IMAGE_BACKEND"] = backend
        self.params = StdioServerParameters(
            command=sys.executable, args=["-m", "carousel.tools.image_server"], env=env
        )

    async def generate(self, image_prompt: str, style_reference: str, output_dir: str) -> str:
        async with stdio_client(self.params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "generate_slide_image",
                    {
                        "image_prompt": image_prompt,
                        "style_reference": style_reference,
                        "output_dir": output_dir,
                    },
                )
                if result.isError:
                    raise RuntimeError(f"generate_slide_image failed: {result.content}")
                return result.content[0].text
