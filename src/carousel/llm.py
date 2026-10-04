"""Thin wrapper around the OpenAI SDK used by every agent."""
from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import TypeVar

from openai import OpenAI
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

# Override with CAROUSEL_MODEL; must support image input + structured outputs.
DEFAULT_MODEL = os.environ.get("CAROUSEL_MODEL", "gpt-6-luna")


class RefusalError(RuntimeError):
    pass


class LLM:
    def __init__(self, model: str = DEFAULT_MODEL, client: OpenAI | None = None,
                 reasoning_effort: str | None = None):
        self.model = model
        # Optional: set CAROUSEL_REASONING (e.g. low) to cut cost/latency on reasoning models.
        self.reasoning_effort = reasoning_effort or os.environ.get("CAROUSEL_REASONING") or None
        self.client = client or OpenAI()  # reads OPENAI_API_KEY

    def parse(self, system: str, user: str | list, schema: type[T], max_tokens: int = 16000) -> T:
        """One structured-output call; returns a validated pydantic instance."""
        kwargs = {}
        if self.reasoning_effort:
            kwargs["reasoning"] = {"effort": self.reasoning_effort}
        response = self.client.responses.parse(
            model=self.model,
            instructions=system,
            input=[{"role": "user", "content": user}],
            text_format=schema,
            max_output_tokens=max_tokens,
            **kwargs,
        )
        for item in response.output:
            if item.type == "message":
                for part in item.content:
                    if part.type == "refusal":
                        raise RefusalError(part.refusal)
        parsed = response.output_parsed
        if parsed is None:
            raise RuntimeError(
                f"Model output was empty or truncated (status={response.status}, "
                f"incomplete={response.incomplete_details})")
        return parsed

    def parse_with_image(self, system: str, text: str, image_path: str | Path,
                         schema: type[T]) -> T:
        media = "image/jpeg" if str(image_path).lower().endswith((".jpg", ".jpeg")) else "image/png"
        b64 = base64.standard_b64encode(Path(image_path).read_bytes()).decode()
        content = [
            {"type": "input_image", "image_url": f"data:{media};base64,{b64}"},
            {"type": "input_text", "text": text},
        ]
        return self.parse(system, content, schema)
