#!/usr/bin/env python3
"""Build app/data/ibge_names.json from an IBGE-derived CSV.

Input CSV format (header required):
    nome,sexo,frequencia
    MARIA,F,11200000
    JOAO,M,2900000
    ...

The script normalizes names (uppercase, strip diacritics, take first token only),
aggregates counts per name by sex, and writes a flat JSON dict to
app/data/ibge_names.json.

Usage:
    python scripts/build_ibge_names.py --csv path/to/ibge_nomes.csv

Source CSV options (download once, manually):
- IBGE 2010 census 'nomes' dataset, available via various community mirrors.
- Or build from the IBGE servicodados API (servicodados.ibge.gov.br/api/v2/censos/nomes)
  by paginating the ranking endpoint per sex and writing rows to a CSV first.
The script does not download — it processes a CSV you provide.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path


def normalize(s: str) -> str:
    if not s:
        return ""
    s = s.strip().upper()
    decomposed = unicodedata.normalize("NFKD", s)
    no_diacritics = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    tokens = [t for t in re.split(r"[\s\-]+", no_diacritics) if t]
    return tokens[0] if tokens else ""


def build(csv_path: Path, out_path: Path) -> None:
    counts: dict[str, dict[str, int]] = defaultdict(lambda: {"f": 0, "m": 0})
    skipped = 0
    rows = 0

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"nome", "sexo", "frequencia"}
        if not required.issubset({h.lower() for h in reader.fieldnames or []}):
            sys.exit(f"CSV must have columns: {sorted(required)}")
        for raw in reader:
            rows += 1
            row = {k.lower(): v for k, v in raw.items()}
            name = normalize(row.get("nome", ""))
            sexo_raw = (row.get("sexo") or "").strip().upper()
            try:
                freq = int(row.get("frequencia") or 0)
            except ValueError:
                skipped += 1
                continue
            if not name or sexo_raw not in {"M", "F"} or freq <= 0:
                skipped += 1
                continue
            key = "f" if sexo_raw == "F" else "m"
            counts[name][key] += freq

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out = {k: dict(v) for k, v in sorted(counts.items())}
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=True, separators=(",", ":"))
        f.write("\n")

    print(f"Read {rows} rows, skipped {skipped}, wrote {len(out)} unique names to {out_path}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--csv", required=True, type=Path, help="Path to IBGE CSV")
    p.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).parent.parent / "app" / "data" / "ibge_names.json",
        help="Output JSON path",
    )
    args = p.parse_args()
    if not args.csv.exists():
        sys.exit(f"CSV not found: {args.csv}")
    build(args.csv, args.out)


if __name__ == "__main__":
    main()
