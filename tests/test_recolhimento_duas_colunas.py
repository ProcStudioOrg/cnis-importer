"""
Regressão: tabela de recolhimentos (facultativo, contribuinte individual, MEI)
impressa em DUAS colunas lado a lado.

O texto linear do PDF traz as duas colunas na mesma linha:

    11/2011 17/11/2011 27,25 545,00 12/2011 21/12/2011 27,25 545,00

Antes da correção, `_parse_facultativo_table` lia UMA competência por linha
(a da esquerda), usava o último valor da linha como salário (o da coluna da
direita) e juntava os indicadores das duas colunas. Um extrato com 180
competências saía com 90, e a competência da esquerda herdava os indicadores
da direita (ex.: 03/2015 pendente recebendo o IREC-FBR de 04/2015).
"""

from app.services.planilha_transformer import transform_to_planilha
from cnis_parser_final import CNISParserFinal

HEADER = ("Competência Data Pgto. Contribuição Salário Contribuição Indicadores "
          "Competência Data Pgto. Contribuição Salário Contribuição Indicadores")


def _make_parser():
    p = CNISParserFinal.__new__(CNISParserFinal)  # sem PDF: teste de unidade
    p.debug = False
    return p


def _facultativo():
    return {"Data": {"Tipo_Filiado_Vinculo": "Facultativo", "Indicadores": ""}, "Remuneracoes": []}


def test_duas_colunas_viram_duas_competencias():
    lines = [
        HEADER,
        "PREC-FBR, IREC- PREC-FBR, IREC-",
        "11/2011 17/11/2011 27,25 545,00 12/2011 21/12/2011 27,25 545,00",
        "LC123 LC123",
        "12/2012 03/01/2013 31,10 622,00 01/2013 08/02/2013 33,90 678,00",
    ]
    emp = _facultativo()
    _make_parser()._parse_facultativo_table(emp, lines, 0)

    assert [r["Competencia"] for r in emp["Remuneracoes"]] == [
        "11/2011", "12/2011", "12/2012", "01/2013"]
    # Cada competência fica com o SEU salário e a SUA contribuição.
    assert [r["Remuneracao"] for r in emp["Remuneracoes"]] == [545.0, 545.0, 622.0, 678.0]
    assert [r["Contribuicao"] for r in emp["Remuneracoes"]] == [27.25, 27.25, 31.10, 33.90]
    assert emp["Remuneracoes"][1]["Data_Pagamento"] == "21/12/2011"


def test_indicador_da_direita_nao_vaza_para_a_esquerda():
    # 03/2015 tem o indicador quebrado em outra linha (vem pela passada de
    # coordenadas); 04/2015 traz o dele na própria linha.
    lines = [
        HEADER,
        "03/2015 09/04/2015 39,40 788,00 04/2015 11/05/2015 39,40 788,00 IREC-FBR, IREC-LC123",
        "05/2015 09/06/2015 39,40 788,00 IREC-FBR, IREC-LC123 06/2015 10/07/2015 39,40 788,00 IREC-FBR, IREC-LC123",
    ]
    emp = _facultativo()
    _make_parser()._parse_facultativo_table(emp, lines, 0)

    por_comp = {r["Competencia"]: r["Indicadores"] for r in emp["Remuneracoes"]}
    assert por_comp == {
        "03/2015": "",
        "04/2015": "IREC-FBR IREC-LC123",
        "05/2015": "IREC-FBR IREC-LC123",
        "06/2015": "IREC-FBR IREC-LC123",
    }


def test_uma_coluna_continua_igual():
    lines = [
        "Competência Data Pgto. Contribuição Salário Contribuição Indicadores",
        "01/2020 10/02/2020 207,80 1.039,00",
        "02/2020 10/03/2020 114,95 1.045,00 IREC-LC123",
    ]
    emp = _facultativo()
    _make_parser()._parse_facultativo_table(emp, lines, 0)

    assert emp["Remuneracoes"] == [
        {"Competencia": "01/2020", "Remuneracao": 1039.0, "Indicadores": "",
         "Contribuicao": 207.80, "Data_Pagamento": "10/02/2020"},
        {"Competencia": "02/2020", "Remuneracao": 1045.0, "Indicadores": "IREC-LC123",
         "Contribuicao": 114.95, "Data_Pagamento": "10/03/2020"},
    ]


def test_planilha_recebe_a_contribuicao():
    result = transform_to_planilha({
        "personal_info": {"Nome": "MARIA SILVA", "CPF": "000.000.000-00",
                          "Data_Nascimento": "01/01/1970"},
        "employment_relationships": [{
            "sequence": 1,
            "Data": {"Origem_Vinculo": "RECOLHIMENTO", "Tipo_Filiado_Vinculo": "Facultativo",
                     "Inicio": "01/11/2011", "Fim": "31/12/2011", "Indicadores": ""},
            "Remuneracoes": [
                {"Competencia": "11/2011", "Remuneracao": 545.0, "Indicadores": "PREC-FBR",
                 "Contribuicao": 27.25, "Data_Pagamento": "17/11/2011"},
                {"Competencia": "12/2011", "Remuneracao": 545.0, "Indicadores": ""},
            ],
        }],
    })
    remus = result["tabs"][0]["periodos"][0]["remuneracoes"]
    assert remus[0] == {"competencia": "11/2011", "valor": 545.0,
                        "indicadores": "PREC-FBR", "contribuicao": 27.25}
    # Vínculo sem valor recolhido (empregado) não ganha o campo.
    assert "contribuicao" not in remus[1]
