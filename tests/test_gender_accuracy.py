"""End-to-end accuracy test for gender inference against a labeled fixture.

Reads downloads/TESTS-GENDER.labels (gitignored), runs each name through
infer_gender, and reports correct / wrong / abstained counts. Fails if any
of the configured thresholds are violated. Skipped when the fixture is absent.
"""

import os
import re
import pytest
from app.utils.gender_inferrer import infer_gender

FIXTURE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "downloads", "TESTS-GENDER.labels"
)

# Pass thresholds from the spec.
MAX_WRONG_RATE = 0.02      # < 2% confidently wrong
MAX_ABSTAIN_RATE = 0.15    # < 15% abstain
MIN_DECIDED_ACCURACY = 0.95  # > 95% accurate among decided

# Map fixture labels (m/f) to inferrer outputs.
LABEL_MAP = {"m": "masculino", "f": "feminino"}


def _parse_fixture(path: str):
    """Yield (full_name, expected_sexo) for each valid line."""
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if ":" not in line:
                continue
            left, _, right = line.rpartition(":")
            label = right.strip().lower()
            if label not in LABEL_MAP:
                continue
            # Take everything before the first "(" — that's the name portion.
            name = re.split(r"\s*\(", left.strip(), maxsplit=1)[0].strip()
            if not name:
                continue
            yield name, LABEL_MAP[label]


@pytest.mark.skipif(
    not os.path.exists(FIXTURE_PATH),
    reason=f"Fixture {FIXTURE_PATH} not present (gitignored, local-only)",
)
def test_accuracy_against_real_cnis_names(capsys):
    correct = 0
    wrong = 0
    abstained = 0
    wrong_cases = []
    total = 0

    for full_name, expected in _parse_fixture(FIXTURE_PATH):
        total += 1
        result = infer_gender(full_name)
        sexo = result["sexo"]
        if sexo == "indeterminado":
            abstained += 1
        elif sexo == expected:
            correct += 1
        else:
            wrong += 1
            wrong_cases.append(
                f"  {result['first_name']:20s} predicted={sexo} expected={expected} ({full_name})"
            )

    assert total > 0, "Fixture parsed zero entries — check format"

    wrong_rate = wrong / total
    abstain_rate = abstained / total
    decided = correct + wrong
    decided_accuracy = (correct / decided) if decided else 0.0

    # Always print breakdown so regressions are visible in CI output.
    with capsys.disabled():
        print()
        print(f"=== Gender accuracy on {total} CNIS names ===")
        print(f"  correct:   {correct} ({correct/total:.1%})")
        print(f"  wrong:     {wrong} ({wrong_rate:.1%})")
        print(f"  abstained: {abstained} ({abstain_rate:.1%})")
        print(f"  accuracy on decided: {decided_accuracy:.1%}")
        if wrong_cases:
            print("Wrong cases:")
            for w in wrong_cases:
                print(w)

    assert wrong_rate < MAX_WRONG_RATE, (
        f"Wrong rate {wrong_rate:.1%} exceeds threshold {MAX_WRONG_RATE:.1%}"
    )
    assert abstain_rate < MAX_ABSTAIN_RATE, (
        f"Abstain rate {abstain_rate:.1%} exceeds threshold {MAX_ABSTAIN_RATE:.1%}"
    )
    assert decided_accuracy > MIN_DECIDED_ACCURACY, (
        f"Decided accuracy {decided_accuracy:.1%} below threshold {MIN_DECIDED_ACCURACY:.1%}"
    )
