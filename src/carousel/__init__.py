"""Transcript -> Instagram carousel multi-agent pipeline."""
import io
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

ENV_PATH = find_dotenv(usecwd=True)  # "" if no .env in the folder you run from
ENV_NAMES: list[str] = []  # setting names found in .env (never the values)


def _read_env_text(path: str) -> str:
    """Decode .env however Windows editors saved it (BOM / UTF-16 / ANSI)."""
    data = Path(path).read_bytes()
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16")
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return data.decode("cp1252", errors="replace")


if ENV_PATH:
    from dotenv import dotenv_values

    _text = _read_env_text(ENV_PATH)
    ENV_NAMES = [k for k in dotenv_values(stream=io.StringIO(_text)) if k]
    # Real environment variables still take priority over .env values.
    load_dotenv(stream=io.StringIO(_text))
