"""Infer sex from a Brazilian given name using a bundled IBGE dataset."""

from __future__ import annotations

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
    tokens = [t for t in re.split(r"[\s\-]+", norm) if t]
    return tokens[0] if tokens else ""
