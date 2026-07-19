"""Tests for CNIS benefit/vínculo type mapping."""

from app.utils.type_mapper import map_tipo_filiado


class TestBeneficioMapping:
    def test_auxilio_doenca(self):
        assert map_tipo_filiado("31 - AUXILIO DOENCA PREVIDENCIARIO") == "AuxilioDoenca"

    def test_aposentadoria_por_invalidez(self):
        assert (
            map_tipo_filiado("32 - APOSENTADORIA POR INVALIDEZ")
            == "AposentadoriaPorInvalidez"
        )

    def test_aposentadoria_invalidez_sem_por(self):
        # Espécie 32 também aparece sem o "POR" no CNIS real.
        assert (
            map_tipo_filiado("32 - APOSENTADORIA INVALIDEZ PREVIDENCIARIA")
            == "AposentadoriaPorInvalidez"
        )

    def test_incapacidade_permanente(self):
        assert (
            map_tipo_filiado("APOSENTADORIA POR INCAPACIDADE PERMANENTE")
            == "AposentadoriaPorInvalidez"
        )

    def test_auxilio_acidente(self):
        assert map_tipo_filiado("94 - AUXILIO ACIDENTE") == "auxilioAcidente"

    def test_salario_maternidade(self):
        assert map_tipo_filiado("80 - SALARIO MATERNIDADE") == "SalarioMaternidade"


class TestVinculoMapping:
    def test_empregado_vira_vazio(self):
        assert map_tipo_filiado("Empregado") == ""

    def test_segurado_especial(self):
        assert map_tipo_filiado("Segurado Especial") == "ruralSeguradoEspecial"

    def test_vazio(self):
        assert map_tipo_filiado("") == ""
