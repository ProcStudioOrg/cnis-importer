# Gender Inference from Brazilian Names — Design

**Date:** 2026-04-21
**Status:** Approved (pending user review of this doc)
**Scope:** Fill the `segurado.sexo` field in the Planilha transformer output by inferring sex from the person's first name. No AI/LLM involved — deterministic lookup against a bundled IBGE 2010 census dataset.

## Problem

`app/services/planilha_transformer.py:72` currently sets `"sexo": ""` with the comment `# CNIS does not contain sex`. The Planilha schema (consumed by ProcStudio) expects this field populated for downstream previdenciário rules where retirement age and contribution rules differ by sex.

CNIS PDFs do not include sex. The only reliable signal we have is `personal_info.Nome`. We will infer from it.

## Non-goals

- Modifying `response_transformer.py` (the `/parse` and `/parse/summary` simple endpoints don't surface sexo and don't need to)
- Cross-checking against `Nome_Mae`
- LLM/ML inference
- Compound first-name disambiguation ("MARIA JOSÉ" vs "JOSÉ MARIA")
- Suffix heuristics for unknown names (e.g. "ends in -a → F"). These fail badly on Brazilian names (Costa, Luca → M; Carmen, Beatriz → F).

## Approach

Bundled offline dataset derived from the IBGE 2010 census *nomes* data. Single dict lookup per parse.

### Why bundled (not API, not curated subset)

- The parser is fully offline today (pdfplumber + local logic). Adding a network call to IBGE per parse breaks that, adds 200–500ms latency, and creates a runtime dependency on IBGE availability and rate limits.
- A curated top-N list misses the long tail of regional Brazilian names (real CNIS examples in `specs/`: *Alquemar*, *Leuzelena*, *Donisete*, *Edemilson*). Coverage matters more than file size.
- Bundled dataset is ~2–3 MB, loaded once, O(1) per lookup, deterministic, reproducible.

## Architecture

### New module: `app/utils/gender_inferrer.py`

Public API:

```python
def infer_gender(nome: str) -> dict:
    """
    Returns:
        {
            "sexo": "masculino" | "feminino" | "indeterminado",
            "confidence": float,   # 0.0 to 1.0
            "first_name": str,     # the normalized token used for lookup
        }
    """
```

Internal:

- `_NAMES: dict[str, dict]` — module-level singleton loaded lazily from `app/data/ibge_names.json` on first call. Format: `{ "ALQUEMAR": {"f": 12, "m": 487}, ... }`. Lazy load (not at import) so test fixtures can stub it.
- `_normalize(nome: str) -> str` — strip whitespace, uppercase, strip diacritics via `unicodedata.normalize("NFKD", ...)` then drop combining marks.
- `_first_name(nome: str) -> str` — `_normalize(nome).split()[0]` after also splitting on hyphens (`re.split(r"[\s-]+", ...)`). Returns `""` for empty/None input.

Decision rule:

1. If `first_name` is empty or not in `_NAMES` → return `indeterminado` with confidence `0.0`.
2. Otherwise compute `total = f + m`, `ratio_f = f / total`, `ratio_m = m / total`.
3. If `max(ratio_f, ratio_m) >= 0.90` → return the dominant sex with `confidence = max(ratio_f, ratio_m)`.
4. Otherwise → `indeterminado` with `confidence = max(ratio_f, ratio_m)`.

The 0.90 threshold is hardcoded (single source of truth as a module constant `_THRESHOLD = 0.90`). Caller cannot override; this is a deliberate choice — INSS context makes a confident wrong answer worse than abstaining, and exposing the knob invites inconsistency across callers.

### Integration point

`app/services/planilha_transformer.py`:

In `transform_to_planilha`, replace:

```python
"sexo": "",  # CNIS does not contain sex
```

with:

```python
"sexo": _infer_sexo_for_planilha(personal.get("Nome") or ""),
```

Where `_infer_sexo_for_planilha` is a thin local helper:

```python
def _infer_sexo_for_planilha(nome: str) -> str:
    result = infer_gender(nome)
    if result["sexo"] == "masculino":
        return "masculino"
    if result["sexo"] == "feminino":
        return "feminino"
    return ""  # Planilha schema is a single string; empty when indeterminado
```

The Planilha schema is a single string with no third state, so `indeterminado` maps to `""` — same as today's behavior. The improvement is positive cases get filled.

### Data file: `app/data/ibge_names.json`

- Format: flat dict mapping normalized uppercase unaccented first name → `{"f": int, "m": int}`.
- Generated once by `scripts/build_ibge_names.py` and committed to the repo.
- Regenerated only when refreshing IBGE data (rare).

### Build script: `scripts/build_ibge_names.py`

Standalone one-off script (not part of runtime). Iterates the IBGE *nomes* API (`https://servicodados.ibge.gov.br/api/v2/censos/nomes`) across letters/pages, accumulates counts per name per sex, normalizes keys (uppercase, strip diacritics), writes the JSON file. Idempotent — running it again produces a deterministic file.

If the IBGE API is unavailable or its shape changes, the script can also accept a local CSV path as fallback (`--csv path/to/nomes.csv` with columns `nome,frequencia,sexo`). This keeps the build reproducible even if upstream changes.

## Error handling

| Input | Output |
|---|---|
| `None` | `{sexo: "indeterminado", confidence: 0.0, first_name: ""}` |
| `""` | same |
| `"   "` | same |
| Name not in dataset | same (confidence 0.0) |
| Ambiguous name (e.g. "DARCI") | `{sexo: "indeterminado", confidence: <ratio>, first_name: "DARCI"}` |
| Confident name | `{sexo: "masculino"|"feminino", confidence: <ratio>, first_name: "..."}` |

No exceptions raised by `infer_gender` for any string input. The data file is loaded lazily; if it's missing, raise a clear `FileNotFoundError` at first call (not at import) — a missing data file is a deployment bug, not a runtime input issue.

## Testing

`tests/test_gender_inferrer.py`:

- **Confident female:** "MARIA", "ANA", "FATIMA", "PETRONILHA" → `feminino`, conf > 0.90
- **Confident male:** "JOÃO", "CARLOS", "ALQUEMAR", "EDEMILSON" → `masculino`, conf > 0.90
- **Ambiguous:** "DARCI", "ARIEL" → `indeterminado`, conf < 0.90 but > 0
- **Unknown:** "ZZNOTAREALNAME" → `indeterminado`, conf 0.0
- **Empty/None:** "", "   ", None → `indeterminado`, conf 0.0, first_name ""
- **Normalization:** "joão", "JOÃO", " João ", "JOAO" all yield identical results
- **Compound first name:** "MARIA JOSÉ DA SILVA" → uses "MARIA"
- **Hyphenated:** "ANA-CLARA SOUZA" → uses "ANA"

`tests/test_planilha_transformer.py` (new or extended):

- Given a parser fixture with `Nome: "ALQUEMAR DA SILVA VARGAS"` → `segurado.sexo == "masculino"`
- Given a parser fixture with `Nome: "MARIA SILVA"` → `segurado.sexo == "feminino"`
- Given a parser fixture with ambiguous/missing name → `segurado.sexo == ""`

The data file used in tests is the real bundled `ibge_names.json` — no mocking. Tests serve as an integration check that the bundled data covers expected names. Specific test names above (PETRONILHA, ALQUEMAR, EDEMILSON) are illustrative — during implementation, verify each against the actual bundled data and swap any that aren't well-represented.

### Accuracy validation against real CNIS names

A separate test (`tests/test_gender_accuracy.py`) measures inference quality against a labeled fixture of real Brazilian CNIS names.

**Fixture file:** `downloads/TESTS-GENDER` — gitignored (PII), maintained locally. Format is one entry per line:

```
ADEMAR FRANCISCO ROMAN (2330) - CNIS - 2025.03.pdf : m
ALICE ALVES RODRIGUES (3316) - CNIS 2025.04.pdf : f
DARCI PEGORARO (2133) - CNIS 2019.02.pdf : m
```

Parser rules:
- Split each line on `:`. Right side is the label (`m` or `f`, case-insensitive, trimmed).
- Left side: extract the leading uppercase name tokens before the first `(` — that's the full name. The `_first_name` helper from the inferrer takes the first token from there.
- Lines that don't match this shape are skipped (with a count reported in the test output).

**Label format:** `m` / `f` only. Mapped at test time: `m → "masculino"`, `f → "feminino"`. The fixture file is the source of truth and must use this format consistently — mixed `male`/`female` entries should be normalized to `m`/`f` before the test runs.

**Test behavior:**
- If the fixture file is absent (CI without local data), the test is **skipped** (not failed) so the rest of the suite still runs.
- If present, the test runs every entry through `infer_gender()` and tallies three buckets:
  - **correct:** inferred sex matches label
  - **wrong:** inferred sex is opposite of label (false confidence — the dangerous bucket)
  - **abstained:** inferred `indeterminado`

**Pass thresholds** (test fails if any are violated):
- `wrong / total < 0.02` — fewer than 2% confidently wrong
- `abstained / total < 0.15` — fewer than 15% abstentions
- `correct / (correct + wrong) > 0.95` — over 95% accuracy on names where we did decide

The test prints the breakdown (counts + percentages) regardless of pass/fail, so a regression is immediately visible. Wrong cases are listed by name so the failure is actionable (e.g. "wrong on ARIEL: predicted masculino, expected feminino").

## Files touched

**New:**
- `app/utils/gender_inferrer.py` — inference module
- `app/data/ibge_names.json` — bundled dataset (committed)
- `app/data/__init__.py` — empty, makes it a package
- `scripts/build_ibge_names.py` — one-off generator
- `tests/test_gender_inferrer.py` — unit tests
- `tests/test_gender_accuracy.py` — accuracy validation against `downloads/TESTS-GENDER`

**Modified:**
- `app/services/planilha_transformer.py` — fill `segurado.sexo` via inferrer
- `tests/test_planilha_transformer.py` — add sexo assertions (create file if not present)

**Unchanged:**
- `app/services/response_transformer.py` — out of scope
- `cnis_parser_final.py` — parser doesn't change
