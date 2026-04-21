"""Integration tests for the Planilha transformer including gender inference."""

from app.services.planilha_transformer import transform_to_planilha


def _parser_result(nome: str) -> dict:
    return {
        "personal_info": {
            "Nome": nome,
            "CPF": "000.000.000-00",
            "Data_Nascimento": "01/01/1970",
        },
        "employment_relationships": [],
    }


class TestSexoInference:
    def test_confident_male_name(self):
        result = transform_to_planilha(_parser_result("CARLOS ALBERTO DA SILVA"))
        assert result["segurado"]["sexo"] == "masculino"

    def test_confident_male_name_regional(self):
        result = transform_to_planilha(_parser_result("EDEMILSON SEMINI"))
        assert result["segurado"]["sexo"] == "masculino"

    def test_confident_female_name(self):
        result = transform_to_planilha(_parser_result("MARIA SILVA"))
        assert result["segurado"]["sexo"] == "feminino"

    def test_ambiguous_name_returns_empty(self):
        result = transform_to_planilha(_parser_result("DARCI PEGORARO"))
        assert result["segurado"]["sexo"] == ""

    def test_unknown_name_returns_empty(self):
        result = transform_to_planilha(_parser_result("ZZNOTAREALNAME"))
        assert result["segurado"]["sexo"] == ""

    def test_missing_name_returns_empty(self):
        result = transform_to_planilha(_parser_result(""))
        assert result["segurado"]["sexo"] == ""

    def test_none_name_returns_empty(self):
        # personal_info has Nome key but value is None
        parser_result = {
            "personal_info": {"Nome": None, "CPF": "", "Data_Nascimento": ""},
            "employment_relationships": [],
        }
        result = transform_to_planilha(parser_result)
        assert result["segurado"]["sexo"] == ""
