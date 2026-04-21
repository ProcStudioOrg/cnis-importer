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
