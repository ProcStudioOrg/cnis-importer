"""
Regression test for the page-break bug in remuneração parsing.

Before the fix, `_parse_regular_remuneracoes` (and the contribuinte/facultativo
table parsers) did `return i` the moment they hit the page footer
("O INSS poderá...") that the INSS injects between PDF pages. A remuneração
table that spans several pages (e.g. a CLT vínculo with ~220 monthly
remunerações) therefore kept only the first page (~30 rows) and silently
dropped the rest. The live production API at procstudio.api.br exhibited the
same loss (e.g. 63 of 223 competências for a real CNIS).

The fix introduces `_skip_page_break`, which steps over the footer + the
repeated page header (INSS / CNIS / Identificação / NIT / Relações
Previdenciárias) and resumes the table, stopping only at the real boundary:
the next vínculo sequence header.
"""

from cnis_parser_final import CNISParserFinal


def _make_parser():
    p = CNISParserFinal.__new__(CNISParserFinal)  # no PDF needed for unit test
    p.debug = False
    return p


def _empty_employment():
    return {"Data": {"Tipo_Filiado_Vinculo": "Empregado", "Indicadores": ""}, "Remuneracoes": []}


def test_regular_remuneracoes_continue_across_page_break():
    # Two competências on page 1, then a full page break (footer + repeated
    # header), then two more competências on page 2, then the next vínculo.
    lines = [
        "  Competência   Remuneração   Indicadores   Competência   Remuneração   Indicadores",
        "     01/2020       1.000,00                    02/2020       1.100,00",
        "O INSS poderá rever a qualquer tempo as informações constantes deste extrato...",
        "O segurado somente terá reconhecida como tempo de contribuição...",
        "                                        INSS",
        "                CNIS - Cadastro Nacional de Informações Sociais",
        "                          Extrato Previdenciário",
        "    Identificação do Filiado",
        "NIT: 123.45678.90-1   CPF: 000.000.000-00   Nome: FULANO DE TAL",
        "Data de nascimento: 01/01/1980",
        "    Relações Previdenciárias",
        "     03/2020       1.200,00                    04/2020       1.300,00",
        # Next vínculo header — pdfplumber emits these without left padding,
        # so the sequence-header regex anchors at column 0.
        "5 123.45678.90-1 80.882.772 PROXIMA EMPRESA LTDA Empregado",
    ]
    p = _make_parser()
    emp = _empty_employment()
    # start_idx points at the "Competência" header row (index 0)
    end = p._parse_regular_remuneracoes(emp, lines, 0)

    comps = [r["Competencia"] for r in emp["Remuneracoes"]]
    # All four competências across the page break must be captured.
    assert comps == ["01/2020", "02/2020", "03/2020", "04/2020"], comps
    # Parsing must stop at the next vínculo sequence header, not run past it.
    assert lines[end].startswith("5 123."), lines[end]


def test_skip_page_break_stops_at_next_vinculo():
    lines = [
        "O INSS poderá rever ...",
        "                                        INSS",
        "    Relações Previdenciárias",
        "9 999.99999.99-9 12.345.678 EMPRESA NOVA Empregado",
    ]
    p = _make_parser()
    # i=0 is the footer; skipping must land on the next vínculo header (idx 3).
    assert p._skip_page_break(lines, 0) == 3


def test_page_validation_complete_doc_no_warning():
    p = _make_parser()
    pages = [f"Página {i} de 3 ... conteúdo da página {i}" for i in range(1, 4)]
    v = p._validate_page_completeness(pages)
    assert v["complete"] is True
    assert v["warnings"] == []


def test_page_validation_flags_truncated_doc():
    p = _make_parser()
    pages = ["Página 1 de 5 conteúdo", "Página 2 de 5 conteúdo"]  # only 2 of 5
    v = p._validate_page_completeness(pages)
    assert v["complete"] is False
    assert any("truncado" in w for w in v["warnings"])


def test_page_validation_flags_empty_page():
    p = _make_parser()
    pages = ["Página 1 de 2 conteúdo", "   "]  # page 2 failed extraction (scanned)
    v = p._validate_page_completeness(pages)
    assert v["complete"] is False
    assert v["empty_pages"] == [2]
