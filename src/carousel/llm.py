"""Thin wrapper around the Gemini SDK used by every agent."""
from __future__ import annotations

import os
from pathlib import Path
from typing import TypeVar

from google import genai
from google.genai import types
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

# Override with CAROUSEL_MODEL; must support image input + JSON/structured output.
DEFAULT_MODEL = os.environ.get("CAROUSEL_MODEL", "gemini-2.5-flash")


class RefusalError(RuntimeError):
    pass


class LLM:
    def __init__(self, model: str = DEFAULT_MODEL, client: genai.Client | None = None):
        self.model = model
        # Reads GEMINI_API_KEY (or GOOGLE_API_KEY) from the environment.
        self.client = client or genai.Client()

    def parse(self, system: str, user: str | list, schema: type[T], max_tokens: int = 16000) -> T:
        """One structured-output call; returns a validated pydantic instance."""
        response = self.client.models.generate_content(
            model=self.model,
            contents=user,
            config=types.GenerateContentConfig(
                system_instruction=system,
                response_mime_type="application/json",
                response_schema=schema,
                max_output_tokens=max_tokens,
            ),
        )
        if response.prompt_feedback and response.prompt_feedback.block_reason:
            raise RefusalError(f"Prompt blocked: {response.prompt_feedback.block_reason}")
        parsed = response.parsed
        if parsed is None:
            reason = response.candidates[0].finish_reason if response.candidates else "no candidates"
            raise RuntimeError(f"Model output was empty, blocked or truncated ({reason})")
        if not isinstance(parsed, schema):  # SDK returned a dict -> validate ourselves
            parsed = schema.model_validate(parsed)
        return parsed

    def parse_with_image(self, system: str, text: str, image_path: str | Path,
                         schema: type[T]) -> T:
        media = "image/jpeg" if str(image_path).lower().endswith((".jpg", ".jpeg")) else "image/png"
        image = types.Part.from_bytes(data=Path(image_path).read_bytes(), mime_type=media)
        return self.parse(system, [image, text], schema)
