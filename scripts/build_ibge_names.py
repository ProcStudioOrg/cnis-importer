#!/usr/bin/env python3
"""Build app/data/ibge_names.json from the turicas/genero-nomes IBGE dataset.

Input CSV format (header required):
    first_name,frequency_female,frequency_male,...

Other columns in the source file (alternative_names, classification,
frequency_total, frequency_group, group_name, ratio) are ignored.

The script normalizes first_name (uppercase, strip diacritics, take first
token only), aggregates counts per normalized name across collisions, and
writes a flat JSON dict to app/data/ibge_names.json.

Usage:
    python scripts/build_ibge_names.py --csv path/to/nomes.csv
    python scripts/build_ibge_names.py --csv path/to/nomes.csv.gz   # .gz auto-detected

Source CSV: turicas/genero-nomes (https://github.com/turicas/genero-nomes),
which itself is derived from IBGE 2010 census + Brasil.IO processing.
The script does not download — it processes a CSV you provide.
"""

from __future__ import annotations

import argparse
import csv
import gzip
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


def _open_csv(csv_path: Path):
    """Open a CSV file as text, transparently handling .gz."""
    if csv_path.suffix == ".gz":
        return gzip.open(csv_path, mode="rt", encoding="utf-8-sig")
    return open(csv_path, encoding="utf-8-sig")


def _to_int(value: str | None) -> int:
    if value is None or value == "":
        return 0
    try:
        return int(value)
    except ValueError:
        return 0


def build(csv_path: Path, out_path: Path) -> None:
    counts: dict[str, dict[str, int]] = defaultdict(lambda: {"f": 0, "m": 0})
    skipped = 0
    rows = 0

    with _open_csv(csv_path) as f:
        reader = csv.DictReader(f)
        required = {"first_name", "frequency_female", "frequency_male"}
        headers = {h.lower() for h in reader.fieldnames or []}
        if not required.issubset(headers):
            sys.exit(f"CSV must have columns: {sorted(required)}; got: {sorted(headers)}")
        for raw in reader:
            rows += 1
            row = {k.lower(): v for k, v in raw.items()}
            name = normalize(row.get("first_name", ""))
            f_count = _to_int(row.get("frequency_female"))
            m_count = _to_int(row.get("frequency_male"))
            if not name or (f_count == 0 and m_count == 0):
                skipped += 1
                continue
            counts[name]["f"] += f_count
            counts[name]["m"] += m_count

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out = {k: dict(v) for k, v in sorted(counts.items())}
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=True, separators=(",", ":"))
        f.write("\n")

    print(f"Read {rows} rows, skipped {skipped}, wrote {len(out)} unique names to {out_path}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--csv", required=True, type=Path, help="Path to IBGE CSV (.csv or .csv.gz)")
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
