"""Thin wrapper around the Anthropic SDK used by every agent."""
from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import TypeVar

import anthropic
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

DEFAULT_MODEL = os.environ.get("CAROUSEL_MODEL", "claude-opus-5-5")


class RefusalError(RuntimeError):
    pass


class LLM:
    def __init__(self, model: str = DEFAULT_MODEL, effort: str = "medium",
                 client: anthropic.Anthropic | None = None):
        self.model = model
        self.effort = effort
        self.client = client or anthropic.Anthropic()

    def parse(self, system: str, user: str | list, schema: type[T], max_tokens: int = 16000) -> T:
        """One structured-output call; returns a validated pydantic instance."""
        response = self.client.messages.parse(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
            output_format=schema,
            output_config={"effort": self.effort},
        )
        if response.stop_reason == "refusal":
            raise RefusalError(f"Model refused: {response.stop_details}")
        if response.stop_reason == "max_tokens" or response.parsed_output is None:
            raise RuntimeError("Model output was truncated or unparsable")
        return response.parsed_output

    def parse_with_image(self, system: str, text: str, image_path: str | Path,
                         schema: type[T]) -> T:
        data = base64.standard_b64encode(Path(image_path).read_bytes()).decode()
        media = "image/jpeg" if str(image_path).lower().endswith((".jpg", ".jpeg")) else "image/png"
        content = [
            {"type": "image", "source": {"type": "base64", "media_type": media, "data": data}},
            {"type": "text", "text": text},
        ]
        return self.parse(system, content, schema)
