"""Infer sex from a Brazilian given name using a bundled IBGE dataset."""

import json
import re
import unicodedata
from pathlib import Path

_THRESHOLD = 0.90
_DATA_PATH = Path(__file__).parent.parent / "data" / "ibge_names.json"
_NAMES: dict | None = None


def _normalize(s: str | None) -> str:
    if not s:
        return ""
    s = s.strip().upper()
    decomposed = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def _first_name(nome: str | None) -> str:
    norm = _normalize(nome)
    if not norm:
        return ""
    tokens = re.split(r"[\s\-]+", norm)
    return tokens[0] if tokens and tokens[0] else ""
