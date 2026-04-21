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


def _load_names() -> dict:
    global _NAMES
    if _NAMES is None:
        with open(_DATA_PATH, encoding="utf-8") as f:
            _NAMES = json.load(f)
    return _NAMES


def infer_gender(nome: str | None) -> dict:
    """Infer sex from a Brazilian name.

    Returns:
        {
            "sexo": "masculino" | "feminino" | "indeterminado",
            "confidence": float,   # 0.0 to 1.0
            "first_name": str,     # normalized lookup key
        }
    """
    first = _first_name(nome)
    if not first:
        return {"sexo": "indeterminado", "confidence": 0.0, "first_name": ""}

    names = _load_names()
    entry = names.get(first)
    if not entry:
        return {"sexo": "indeterminado", "confidence": 0.0, "first_name": first}

    f = entry.get("f", 0)
    m = entry.get("m", 0)
    total = f + m
    if total == 0:
        return {"sexo": "indeterminado", "confidence": 0.0, "first_name": first}

    ratio_f = f / total
    ratio_m = m / total
    top = max(ratio_f, ratio_m)

    if top >= _THRESHOLD:
        sexo = "feminino" if ratio_f > ratio_m else "masculino"
    else:
        sexo = "indeterminado"

    return {"sexo": sexo, "confidence": top, "first_name": first}
