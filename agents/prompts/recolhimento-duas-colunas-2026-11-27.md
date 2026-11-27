# Recolhimentos em duas colunas: leitor perdia metade das competências (27/11/2026)

Pedido direto do Bruno, a partir de uma planilha de produção do ProcStudio
(facultativo baixa renda, 180 competências de 11/2011 a 10/2026).

## Sintoma

A planilha mostrava 90 competências em vez de 180 e `PREC-FBR ×21` onde o extrato tem 41.
A competência 03/2015 (pendente, `PREC-FBR`) vinha também com `IREC-FBR`.

## Causa

O extrato imprime a tabela de recolhimentos em duas colunas lado a lado. No texto linear do
PDF as duas saem na mesma linha:

    11/2011 17/11/2011 27,25 545,00 12/2011 21/12/2011 27,25 545,00

`_parse_facultativo_table` lia uma competência por linha: a da esquerda (`parts[0]`), com o
ÚLTIMO valor da linha como salário (o da coluna da direita) e os indicadores das duas colunas
juntos. A passada por coordenadas (`_enriquece_indicadores_por_coordenadas`) calculava certo os
indicadores da coluna da direita, mas só os aplica a competências que já existem.

A função é escolhida pelo cabeçalho ("Salário Contribuição"), não pelo tipo de filiado: vale
para facultativo, contribuinte individual e MEI em carnê.

## Correção

- `_segmentos_por_competencia`: quebra a linha em um segmento por competência (MM/AAAA que não
  é parte de uma data DD/MM/AAAA). Usada em `_parse_facultativo_table` e, pela mesma razão, em
  `_parse_contribuinte_individual_table`.
- Cada remuneração de recolhimento passa a levar `Contribuicao` (valor pago) e `Data_Pagamento`.
- `planilha_transformer` repassa `contribuicao` à planilha; o ProcStudio (PR #1268) usa o campo
  para calcular a alíquota paga. Campo novo e opcional: quem não conhece ignora.

## Resultado no extrato do caso

180 competências, 41 `PREC-FBR IREC-LC123` + 139 `IREC-FBR IREC-LC123`, contribuição = 5% do
salário em todas, `All_Competences_Complete: true`.

## Efeito em produção

Planilhas já importadas guardam o que o leitor entregou na época: precisam reimportar o CNIS.
`tests/test_api.py::TestValidation` (2 testes) já falha na `main` com 403 — sem relação.
