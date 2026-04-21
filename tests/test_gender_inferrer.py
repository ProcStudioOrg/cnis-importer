"""Tests for the gender inferrer module."""

import pytest
from app.utils import gender_inferrer
from app.utils.gender_inferrer import _normalize, _first_name


class TestNormalize:
    def test_uppercases(self):
        assert _normalize("joao") == "JOAO"

    def test_strips_diacritics(self):
        assert _normalize("João") == "JOAO"
        assert _normalize("FÁTIMA") == "FATIMA"

    def test_strips_whitespace(self):
        assert _normalize("  Joao  ") == "JOAO"

    def test_handles_empty(self):
        assert _normalize("") == ""

    def test_handles_none(self):
        assert _normalize(None) == ""


class TestFirstName:
    def test_takes_first_token(self):
        assert _first_name("MARIA JOSÉ DA SILVA") == "MARIA"

    def test_normalizes(self):
        assert _first_name("joão silva") == "JOAO"

    def test_splits_on_hyphen(self):
        assert _first_name("ANA-CLARA SOUZA") == "ANA"

    def test_handles_empty(self):
        assert _first_name("") == ""
        assert _first_name(None) == ""

    def test_handles_whitespace_only(self):
        assert _first_name("   ") == ""

    def test_strips_leading_separators(self):
        assert _first_name("-CLARA SOUZA") == "CLARA"
        assert _first_name(" - MARIA") == "MARIA"


class TestInferGender:
    @pytest.fixture(autouse=True)
    def stub_names(self, monkeypatch):
        # Inject a controlled dataset for unit tests.
        monkeypatch.setattr(gender_inferrer, "_NAMES", {
            "MARIA": {"f": 11_200_000, "m": 5_400},
            "JOAO": {"f": 1_200, "m": 2_900_000},
            "ALQUEMAR": {"f": 12, "m": 487},
            "DARCI": {"f": 4_800, "m": 5_100},   # ambiguous
            "ARIEL": {"f": 2_000, "m": 3_000},   # ambiguous (60/40)
        })

    def test_confident_female(self):
        r = gender_inferrer.infer_gender("MARIA SILVA")
        assert r["sexo"] == "feminino"
        assert r["confidence"] > 0.99
        assert r["first_name"] == "MARIA"

    def test_confident_male(self):
        r = gender_inferrer.infer_gender("João da Silva")
        assert r["sexo"] == "masculino"
        assert r["confidence"] > 0.99
        assert r["first_name"] == "JOAO"

    def test_confident_male_regional(self):
        r = gender_inferrer.infer_gender("ALQUEMAR DA SILVA VARGAS")
        assert r["sexo"] == "masculino"
        assert r["confidence"] >= 0.90

    def test_ambiguous_50_50(self):
        r = gender_inferrer.infer_gender("DARCI PEGORARO")
        assert r["sexo"] == "indeterminado"
        assert 0 < r["confidence"] < 0.90

    def test_ambiguous_60_40(self):
        r = gender_inferrer.infer_gender("ARIEL SOUZA")
        assert r["sexo"] == "indeterminado"
        assert 0 < r["confidence"] < 0.90

    def test_unknown_name(self):
        r = gender_inferrer.infer_gender("ZZNOTAREALNAME")
        assert r["sexo"] == "indeterminado"
        assert r["confidence"] == 0.0
        assert r["first_name"] == "ZZNOTAREALNAME"

    def test_empty_input(self):
        r = gender_inferrer.infer_gender("")
        assert r["sexo"] == "indeterminado"
        assert r["confidence"] == 0.0
        assert r["first_name"] == ""

    def test_none_input(self):
        r = gender_inferrer.infer_gender(None)
        assert r["sexo"] == "indeterminado"
        assert r["confidence"] == 0.0
        assert r["first_name"] == ""

    def test_normalization_consistency(self):
        a = gender_inferrer.infer_gender("joão")
        b = gender_inferrer.infer_gender("JOÃO")
        c = gender_inferrer.infer_gender(" João ")
        d = gender_inferrer.infer_gender("JOAO")
        assert a == b == c == d


class TestLazyLoad:
    def test_load_raises_filenotfound_when_data_missing(self, monkeypatch, tmp_path):
        # Reset the cached singleton and point at a nonexistent file.
        monkeypatch.setattr(gender_inferrer, "_NAMES", None)
        monkeypatch.setattr(gender_inferrer, "_DATA_PATH", tmp_path / "nope.json")
        with pytest.raises(FileNotFoundError):
            gender_inferrer.infer_gender("MARIA")

    def test_load_caches_after_first_call(self, monkeypatch, tmp_path):
        # Write a tiny data file, call twice, ensure file is opened only once.
        data_file = tmp_path / "tiny.json"
        data_file.write_text('{"MARIA": {"f": 100, "m": 0}}')
        monkeypatch.setattr(gender_inferrer, "_NAMES", None)
        monkeypatch.setattr(gender_inferrer, "_DATA_PATH", data_file)

        open_calls = []
        original_open = open
        def counting_open(*args, **kwargs):
            open_calls.append(args[0])
            return original_open(*args, **kwargs)
        monkeypatch.setattr("builtins.open", counting_open)

        gender_inferrer.infer_gender("MARIA")
        gender_inferrer.infer_gender("MARIA")

        json_opens = [c for c in open_calls if str(c).endswith("tiny.json")]
        assert len(json_opens) == 1
