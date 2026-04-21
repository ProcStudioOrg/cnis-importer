"""Transforms parser output into ProcStudio Planilha.spreadsheet_data schema."""

import secrets
from app.utils.type_mapper import map_tipo_filiado, is_beneficio
from app.utils.gender_inferrer import infer_gender


def _generate_uid():
    return f"p-{secrets.token_hex(4)}"


def _is_beneficio_row(data: dict) -> bool:
    """Treat a row as a benefit when the parser flagged it, or when legacy
    tipo/origem strings mention 'Benefício'."""
    if data.get("Is_Beneficio"):
        return True
    tipo = data.get("Tipo_Filiado_Vinculo") or ""
    origem = data.get("Origem_Vinculo") or ""
    return is_beneficio(tipo) or is_beneficio(origem)


def _beneficio_name(data: dict) -> str:
    """Full benefit name, preferring the parser's Especie, with legacy fallback."""
    especie = (data.get("Especie") or "").strip()
    if especie:
        return especie
    tipo = (data.get("Tipo_Filiado_Vinculo") or "").replace("Benefício", "").strip()
    return tipo or (data.get("Origem_Vinculo") or "").strip()


def _transform_periodo(seq: int, emp: dict) -> dict:
    data = emp.get("Data", {})
    tipo = data.get("Tipo_Filiado_Vinculo") or ""
    origem = data.get("Origem_Vinculo") or ""
    inicio = data.get("Inicio") or ""
    fim = data.get("Fim") or ""
    beneficio = _is_beneficio_row(data)

    if beneficio:
        name = _beneficio_name(data)
        atividade_tipo = map_tipo_filiado(tipo) or map_tipo_filiado(
            data.get("Especie") or origem
        )
    else:
        name = origem
        atividade_tipo = map_tipo_filiado(tipo)

    meta = {
        "tipoVinculo": tipo or ("Benefício" if beneficio else ""),
        "codigoEmpresa": "" if beneficio else (data.get("Codigo_Empresa") or ""),
        "indicadores": data.get("Indicadores") or "",
        "totalRemuneracoes": len(emp.get("Remuneracoes", [])),
        "inicioCnis": inicio,
        "fimCnis": fim,
    }
    if beneficio:
        meta["nb"] = data.get("NB") or ""
        meta["especie"] = (data.get("Especie") or "").strip()
        meta["situacao"] = data.get("Situacao") or ""

    return {
        "uid": _generate_uid(),
        "seq": seq,
        "name": name,
        "inicio": inicio,
        "fim": fim,
        "ativo": True,
        "beneficio": beneficio,
        "atividadeTipo": atividade_tipo,
        "especial": "normal",
        "contaParaCarencia": True,
        "fatorPersonalizadoDoEspecial": None,
        "indenizouRuralSeguradoEspecialApos31101991": False,
        "complementouAliquotaReduzida": False,
        "grauDeficiencia": None,
        "meta": meta,
    }


def _should_park_in_analysis(periodo: dict) -> bool:
    """Route a benefit to the analysis array when it cannot count as
    contribution time: either it was denied (INDEFERIDO) or it has no start
    date to place on a timeline. Benefits that are merely ongoing (inicio set,
    fim empty) stay in the main periodos list.
    """
    if not periodo.get("beneficio"):
        return False
    situacao = (periodo.get("meta", {}).get("situacao") or "").upper()
    if situacao == "INDEFERIDO":
        return True
    return not periodo.get("inicio")


def _infer_sexo_for_planilha(nome: str) -> str:
    result = infer_gender(nome)
    if result["sexo"] == "masculino":
        return "masculino"
    if result["sexo"] == "feminino":
        return "feminino"
    return ""


def transform_to_planilha(parser_result: dict) -> dict:
    """Transform parser output to Planilha.spreadsheet_data schema.

    Returns a dict that can be directly stored in Planilha.spreadsheet_data (JSONB).
    Benefits with full dates go into `periodos` with `beneficio: true`; benefits
    lacking dates (e.g. INDEFERIDO) are routed to `situacoesAAnalisar`.
    """
    personal = parser_result.get("personal_info", {})
    empls = parser_result.get("employment_relationships", [])

    all_rows = [_transform_periodo(i + 1, emp) for i, emp in enumerate(empls)]
    periodos = [p for p in all_rows if not _should_park_in_analysis(p)]
    situacoes = [p for p in all_rows if _should_park_in_analysis(p)]

    return {
        "segurado": {
            "cpf": personal.get("CPF") or "",
            "nome": personal.get("Nome") or "",
            "sexo": _infer_sexo_for_planilha(personal.get("Nome") or ""),
            "dataDeNascimento": personal.get("Data_Nascimento") or "",
            "customerUuid": "",
        },
        "tabs": [
            {
                "uid": "tab-1",
                "label": "CNIS Import",
                "der": "",
                "reafirmacaoDer": "",
                "sistema": "rgps",
                "periodos": periodos,
                "periodosDeficiencia": [],
                "situacoesAAnalisar": situacoes,
            }
        ],
        "activeTabUid": "tab-1",
        "config": {"mostrarRegrasPreReforma": False},
    }
