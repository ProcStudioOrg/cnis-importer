/**
 * Tabela de tradução dos INDICADORES DO CNIS (extrato previdenciário do INSS).
 *
 * Fonte primária: Anexo V da Portaria DIRBEN/INSS nº 990, de 28/03/2022
 * (alterada pela Portaria DIRBEN/INSS nº 1.316, de 24/11/2025) —
 * "Relação dos Indicadores disponibilizados no CNIS":
 * https://portalin.inss.gov.br/assets/anexos/pt990/AnexoV.pdf
 *
 * Fontes complementares: legenda oficial impressa no fim de 250 extratos CNIS
 * reais (base PROCSTUDIO-CNIS-DATA, varrida em 07/2026) e fontes previdenciárias
 * secundárias (Cálculo Jurídico, Ingrácio, Bocchi, Previdenciarista).
 *
 * Convenção dos prefixos:
 *   P*  = Pendência  — impede ou condiciona o cômputo; exige tratamento/comprovação
 *   I*  = Alerta     — informativo; alguns condicionam o cômputo (ex.: LC 123)
 *   A*  = Acerto     — resultado de requerimento de acerto (deferido/indeferido)
 *
 * Este arquivo é standalone (sem dependências) para uso no frontend.
 */

export type CnisIndicadorTipo = "pendencia" | "alerta" | "acerto" | "cadastro";

export type CnisIndicadorNivel = "vinculo" | "remuneracao" | "ambos";

/** Efeito sobre a contagem de tempo/carência/valor do benefício. */
export type CnisBloqueio =
  | "sim" // competência/vínculo NÃO conta enquanto não tratado/comprovado
  | "condicional" // conta para alguns fins, ou depende de complementação/análise
  | "nao"; // meramente informativo

export interface CnisIndicador {
  codigo: string;
  /** Texto oficial (Anexo V / legenda do extrato). */
  descricaoOficial: string;
  /** Explicação prática para o advogado/segurado. */
  explicacao: string;
  tipo: CnisIndicadorTipo;
  nivel: CnisIndicadorNivel;
  bloqueiaComputo: CnisBloqueio;
  /** true = apareceu na base real de 250 CNIS da ProcStudio. */
  vistoNaBase: boolean;
}

const I = (
  codigo: string,
  descricaoOficial: string,
  explicacao: string,
  tipo: CnisIndicadorTipo,
  nivel: CnisIndicadorNivel,
  bloqueiaComputo: CnisBloqueio,
  vistoNaBase = false,
): CnisIndicador => ({
  codigo,
  descricaoOficial,
  explicacao,
  tipo,
  nivel,
  bloqueiaComputo,
  vistoNaBase,
});

export const CNIS_INDICADORES: Record<string, CnisIndicador> = {
  // ────────────────────────────────────────────────────────────────────────
  // Indicadores "guarda-chuva" (nível de vínculo)
  // ────────────────────────────────────────────────────────────────────────
  "IREM-INDPEND": I(
    "IREM-INDPEND",
    "Remunerações com indicadores/pendências",
    "Alguma remuneração deste vínculo tem alerta ou pendência. É preciso detalhar as competências para achar o indicador específico (PREM-FVIN, PREM-EXT etc.).",
    "alerta",
    "vinculo",
    "condicional",
    true,
  ),
  "IREC-INDPEND": I(
    "IREC-INDPEND",
    "Recolhimentos com indicadores/pendências",
    "Análogo ao IREM-INDPEND, para contribuinte individual/facultativo/segurado especial: alguma competência do período tem indicador. Detalhar cada salário de contribuição.",
    "alerta",
    "vinculo",
    "condicional",
    true,
  ),

  // ────────────────────────────────────────────────────────────────────────
  // Plano Simplificado / MEI (LC 123/2006) e salário mínimo
  // ────────────────────────────────────────────────────────────────────────
  "IREC-LC123": I(
    "IREC-LC123",
    "Recolhimento no Plano Simplificado de Previdência Social (LC 123/2006) — alíquotas reduzidas de 11% e 5%",
    "Sem complementação para 20% (GPS cód. 1295), a competência NÃO conta para aposentadoria por tempo de contribuição nem CTC; vale para aposentadoria por idade e carência.",
    "alerta",
    "remuneracao",
    "condicional",
    true,
  ),
  "IREC-MEI": I(
    "IREC-MEI",
    "Indica que a contribuição da competência foi recolhida com código MEI",
    "Contribuição de 5% do MEI (via DAS). Mesma restrição do IREC-LC123: sem complementação para 20% (GPS cód. 1910), não vale para tempo de contribuição/CTC.",
    "alerta",
    "remuneracao",
    "condicional",
    true,
  ),
  "IREC-LC123-SUP": I(
    "IREC-LC123-SUP",
    "Recolhimento no Plano Simplificado superior ao salário mínimo",
    "Pagou 11%/5% sobre base MAIOR que o salário mínimo. No plano simplificado o salário de contribuição é sempre limitado ao mínimo: o excedente é desprezado (cabe restituição na RFB).",
    "alerta",
    "remuneracao",
    "nao",
  ),
  "IREC-LIM-SM": I(
    "IREC-LIM-SM",
    "Indica que a contribuição da competência foi limitada ao salário mínimo",
    "Efeito do recolhimento acima do limite do plano: o sistema capou o salário de contribuição no mínimo. Par causa/efeito com IREC-LC123-SUP. Equivalente PRISMA/SABI: ISALMIN.",
    "alerta",
    "remuneracao",
    "nao",
    true,
  ),
  "PREC-MENOR-MIN": I(
    "PREC-MENOR-MIN",
    "Recolhimento abaixo do valor mínimo",
    "Recolhimento inferior ao salário mínimo da competência (§3º art. 214, Dec. 3.048/99). Sem complementação, NÃO conta para tempo, carência nem cálculo. A partir da competência 11/2019 é substituído por PSC-MEN-SM-EC103.",
    "pendencia",
    "remuneracao",
    "sim",
    true,
  ),
  "PSC-MEN-SM-EC103": I(
    "PSC-MEN-SM-EC103",
    "Competência com somatório dos salários de contribuição menor que o mínimo, passível de complementação, utilização ou agrupamento (EC 103/2019)",
    "Vigente para competências a partir de 11/2019 (art. 29 da EC 103). Não conta até o ajuste: complementar via DARF (receita 1872-02), utilizar excedente de outra competência ou agrupar competências do mesmo ano civil, pelo Meu INSS.",
    "pendencia",
    "remuneracao",
    "sim",
    true,
  ),
  ISALMIN: I(
    "ISALMIN",
    "Contribuição da competência foi limitada ao salário mínimo",
    "Versão PRISMA/SABI do IREC-LIM-SM.",
    "alerta",
    "remuneracao",
    "nao",
  ),

  // ────────────────────────────────────────────────────────────────────────
  // Ajustes da EC 103/2019 (complementação / utilização / agrupamento)
  // ────────────────────────────────────────────────────────────────────────
  "ICOMPL-VR-SM-EC103": I(
    "ICOMPL-VR-SM-EC103",
    "Competência possui recolhimento de complementação (DARF) para o valor mínimo",
    "Complementação da EC 103 efetuada — a competência passou a valer.",
    "alerta",
    "remuneracao",
    "nao",
    true,
  ),
  "IAGRUP-SM-EC103": I(
    "IAGRUP-SM-EC103",
    "Competência agrupada resultou em valor igual ao salário mínimo",
    "Rastreio das movimentações de agrupamento do art. 29 da EC 103. Variantes: IAGRUP-MN-SM-EC103 (recebeu valor mas ficou abaixo do mínimo), IAGRUP-VR-EC103 (restou valor residual), IAGRUP-ZER-EC103 (restou zerada).",
    "alerta",
    "remuneracao",
    "nao",
    true,
  ),
  "IAGRUP-MN-SM-EC103": I(
    "IAGRUP-MN-SM-EC103",
    "Competência recebeu valor por agrupamento mas permaneceu abaixo do mínimo",
    "Ajuste EC 103 parcial — ainda não conta.",
    "alerta",
    "remuneracao",
    "condicional",
  ),
  "IAGRUP-VR-EC103": I(
    "IAGRUP-VR-EC103",
    "Competência cedeu valor em agrupamento e restou valor residual",
    "Ajuste EC 103 — rastreio de movimentação.",
    "alerta",
    "remuneracao",
    "nao",
  ),
  "IAGRUP-ZER-EC103": I(
    "IAGRUP-ZER-EC103",
    "Competência cedeu todo o valor em agrupamento e restou zerada",
    "Ajuste EC 103 — a competência doadora deixa de contar.",
    "alerta",
    "remuneracao",
    "nao",
  ),
  "IUTILIZ-EXC-EC103": I(
    "IUTILIZ-EXC-EC103",
    "Competência foi favorecida por utilização de excedente de outra competência",
    "Ajuste EC 103 concluído em favor desta competência. Variante IUTILIZ-EXC-MN-SM-EC103: favorecida mas permaneceu abaixo do mínimo.",
    "alerta",
    "remuneracao",
    "nao",
    true,
  ),
  "ICED-VR-EXC-EC103": I(
    "ICED-VR-EXC-EC103",
    "Competência cedeu valor excedente para outra competência",
    "Ajuste EC 103 — rastreio da competência doadora.",
    "alerta",
    "remuneracao",
    "nao",
    true,
  ),
  "IVLR-DARF-LIMITADO": I(
    "IVLR-DARF-LIMITADO",
    "Valor de DARF limitado para não ultrapassar o salário mínimo na competência",
    "Acompanha ICOMPL-VR-SM-EC103.",
    "alerta",
    "remuneracao",
    "nao",
  ),
  "IREL-PREV-POSSUI-COMP-AJUST": I(
    "IREL-PREV-POSSUI-COMP-AJUST",
    "Relação previdenciária possui competência ajustada (favorecida/desfavorecida)",
    "Indicador de vínculo: alguma competência do período sofreu ajuste da EC 103.",
    "alerta",
    "vinculo",
    "nao",
    true,
  ),

  // ────────────────────────────────────────────────────────────────────────
  // Extemporaneidade (informação fora do prazo)
  // ────────────────────────────────────────────────────────────────────────
  PEXT: I(
    "PEXT",
    "Vínculo com informação extemporânea, passível de comprovação",
    "Vínculo inserido fora do prazo legal (art. 19, §3º do RPS). Sem comprovação documental, não conta para tempo nem entra no cálculo.",
    "pendencia",
    "vinculo",
    "sim",
    true,
  ),
  "PREM-EXT": I(
    "PREM-EXT",
    "Remuneração informada fora do prazo, passível de comprovação",
    "GFIP/eSocial extemporânea (competências ≥ 04/2003). Não conta sem comprovação (art. 29-A, Lei 8.213/91).",
    "pendencia",
    "remuneracao",
    "sim",
    true,
  ),
  IEAN: I(
    "IEAN",
    "Exposição a agente nocivo informada pelo empregador, passível de comprovação",
    "Forte indício de atividade especial: o próprio empregador declarou o adicional do art. 22, II, da Lei 8.212/91 (GILRAT) em GFIP/eSocial. Aparece como IEAN (15/20/25) conforme os anos exigidos. NÃO gera enquadramento automático — o INSS ainda exige PPP/LTCAT.",
    "alerta",
    "vinculo",
    "condicional",
    true,
  ),

  // ────────────────────────────────────────────────────────────────────────
  // Remunerações inconsistentes com o vínculo
  // ────────────────────────────────────────────────────────────────────────
  "PREM-FVIN": I(
    "PREM-FVIN",
    "Remuneração após o fim do vínculo",
    "Competência posterior à rescisão registrada — não computada. Verificar erro na data de rescisão (o vínculo recebe IREM-INDPEND).",
    "pendencia",
    "remuneracao",
    "sim",
    true,
  ),
  "PREM-IVIN": I(
    "PREM-IVIN",
    "Remuneração antes do início do vínculo",
    "Competência anterior à admissão registrada — não computada. Verificar erro na data de admissão.",
    "pendencia",
    "remuneracao",
    "sim",
    true,
  ),
  "PREM-EMPR": I(
    "PREM-EMPR",
    "Remuneração fora do período de atividade do empregador (antes do início ou após o encerramento)",
    "Impede o cômputo da competência; corrigir dados do empregador na RFB.",
    "pendencia",
    "remuneracao",
    "sim",
    true,
  ),
  "PREM-OBITO": I(
    "PREM-OBITO",
    "Remuneração após o óbito do filiado",
    "Só contam remunerações até a competência do óbito.",
    "pendencia",
    "remuneracao",
    "sim",
  ),
  "PREM-NASC": I(
    "PREM-NASC",
    "Remuneração anterior à data de nascimento do filiado",
    "Erro de competência ou de cadastro.",
    "pendencia",
    "remuneracao",
    "sim",
  ),

  // ────────────────────────────────────────────────────────────────────────
  // Dados do empregador / do vínculo
  // ────────────────────────────────────────────────────────────────────────
  "PADM-EMPR": I(
    "PADM-EMPR",
    "Data de admissão anterior ao início (ou posterior ao encerramento) da atividade do empregador",
    "Não impede o cômputo se comprovado/validado via acerto (VRE).",
    "pendencia",
    "vinculo",
    "condicional",
    true,
  ),
  "PRES-EMPR": I(
    "PRES-EMPR",
    "Data de rescisão posterior ao encerramento (ou anterior ao início) da atividade do empregador",
    "Análogo ao PADM-EMPR.",
    "pendencia",
    "vinculo",
    "condicional",
    true,
  ),
  "PEMP-CAD": I(
    "PEMP-CAD",
    "Faltam dados cadastrais do empregador (CNPJ ou CEI)",
    "O vínculo exige comprovação documental da relação de trabalho.",
    "pendencia",
    "vinculo",
    "condicional",
    true,
  ),
  "PEMP-IDINV": I(
    "PEMP-IDINV",
    "Empregador com identificador inválido",
    "Identificador CPF/INCRA/PASEP/CI/Ignorado (comum em vínculos das décadas de 70/80); exige comprovação.",
    "pendencia",
    "vinculo",
    "condicional",
    true,
  ),
  "PVIN-IRREG": I(
    "PVIN-IRREG",
    "Vínculo em situação de irregularidade",
    "Marcação resultante de apuração de indício de FRAUDE. Vínculo/remuneração não considerado até desmarcação.",
    "pendencia",
    "vinculo",
    "sim",
  ),
  PRPPS: I(
    "PRPPS",
    "Vínculo de empregado com informações de Regime Próprio de Previdência (servidor público)",
    "Período RPPS (total ou parcial) não conta no RGPS sem ajuste/análise (arts. 68-69 da IN 128/2022). Se o tempo for usado no regime próprio, é preciso excluir do RGPS (e vice-versa, via CTC).",
    "pendencia",
    "vinculo",
    "condicional",
    true,
  ),
  PRPSE: I(
    "PRPSE",
    "Vínculo de empregado em Regime de Previdência no Exterior",
    "Expatriado; sem reflexo no RGPS. Correção só pelo empregador no eSocial.",
    "pendencia",
    "vinculo",
    "sim",
  ),
  "PDT-NASC-FIL-INV": I(
    "PDT-NASC-FIL-INV",
    "Idade do filiado menor que a permitida pela legislação (12/14/16 anos)",
    "Períodos anteriores à idade mínima legal não são considerados, salvo análise pontual (trabalho infantil comprovado costuma ser reconhecido judicialmente).",
    "pendencia",
    "vinculo",
    "condicional",
    true,
  ),
  "PEMP-SEQ-IGN": I(
    "PEMP-SEQ-IGN",
    "Sequência de vínculo com empregador ignorado",
    "Cadastral; exige comprovação.",
    "pendencia",
    "vinculo",
    "condicional",
  ),
  NDET: I(
    "NDET",
    "Data de início de atividade estimada na migração (RAIS antiga informava só mês/ano)",
    "Comprovar o vínculo na forma da IN 128/2022 se a data exata importar.",
    "pendencia",
    "vinculo",
    "condicional",
  ),

  // ────────────────────────────────────────────────────────────────────────
  // Recolhimentos (contribuinte individual / facultativo)
  // ────────────────────────────────────────────────────────────────────────
  "PREC-FACULTCONC": I(
    "PREC-FACULTCONC",
    "Recolhimento de contribuinte facultativo concomitante com outros vínculos",
    "Facultativo é vedado a quem tem filiação obrigatória no período. Recolhimento não considerado até ajuste (alterar código) ou restituição.",
    "pendencia",
    "remuneracao",
    "sim",
    true,
  ),
  "PREC-CDCONC": I(
    "PREC-CDCONC",
    "Recolhimento de contribuinte em dobro concomitante com outro vínculo",
    "Contribuição duplicada na competência; pode caber restituição na RFB.",
    "pendencia",
    "remuneracao",
    "sim",
  ),
  "PREC-CSE": I(
    "PREC-CSE",
    "Recolhimento de segurado especial pendente de comprovação da atividade",
    "GPS 1503/carnê de segurado especial sem homologação da atividade rural; não conta até ratificação.",
    "pendencia",
    "remuneracao",
    "sim",
    true,
  ),
  "PREC-PMIG-DOM": I(
    "PREC-PMIG-DOM",
    "Recolhimento de empregado doméstico sem comprovação do vínculo",
    "GPS de doméstico sem vínculo correspondente no CNIS; incluir o vínculo via acerto (VRE).",
    "pendencia",
    "remuneracao",
    "condicional",
    true,
  ),
  "PREC-LC150-DOM": I(
    "PREC-LC150-DOM",
    "Pagamento de doméstico em GPS em período com remuneração de fonte eSocial",
    "GPS de doméstico a partir de 10/2015 é indevida (era do DAE/eSocial); cabe restituição.",
    "pendencia",
    "remuneracao",
    "sim",
    true,
  ),
  "PREC-OBITO": I(
    "PREC-OBITO",
    "Competência do recolhimento posterior ao mês do óbito",
    "Só contam competências até o óbito, pagas antes do falecimento.",
    "pendencia",
    "remuneracao",
    "sim",
  ),
  "PREC-COD1821": I(
    "PREC-COD1821",
    "Recolhimento com código de pagamento 1821 (mandato eletivo)",
    "Falta complementação para 20% (período 02/1998 a 18/09/2004).",
    "pendencia",
    "remuneracao",
    "condicional",
  ),
  IRECOL: I(
    "IRECOL",
    "Contribuição da competência é recolhimento (GPS)",
    "Meramente descritivo (extrato PRISMA/SABI). Pode vir qualificado: IRECOL (ILEI123) = plano simplificado 11%; IRECOL (IMEI) = MEI.",
    "alerta",
    "remuneracao",
    "nao",
  ),
  "IREC-DESINDEXA": I(
    "IREC-DESINDEXA",
    "Contribuição da competência foi desindexada",
    "Recolhimento em atraso já corrigido monetariamente; evita dupla correção. Sem tratamento.",
    "alerta",
    "remuneracao",
    "nao",
    true,
  ),

  // ────────────────────────────────────────────────────────────────────────
  // Facultativo Baixa Renda (Lei 12.470/2011, alíquota 5%)
  // ────────────────────────────────────────────────────────────────────────
  "IREC-FBR": I(
    "IREC-FBR",
    "Recolhimento de segurado Facultativo de Baixa Renda já validado",
    "Contribuição de 5% validada: conta para idade e carência; NÃO conta para tempo de contribuição sem complementação.",
    "alerta",
    "remuneracao",
    "condicional",
    true,
  ),
  "PREC-FBR": I(
    "PREC-FBR",
    "Recolhimento de segurado Facultativo de Baixa Renda não validado / pendente de análise",
    "Aguarda validação (CadÚnico, renda familiar ≤ 2 SM etc.). Sem validação nem complementação (GPS 1830 p/ 11% ou 1945 p/ 20%), não conta.",
    "pendencia",
    "remuneracao",
    "sim",
    true,
  ),
  "PREC-FBR-ANT": I(
    "PREC-FBR-ANT",
    "Recolhimento de Facultativo Baixa Renda anterior a 09/2011 (inválido)",
    "A modalidade só existe desde a Lei 12.470/2011; alterar código para plano simplificado (11%) ou 20% e recolher a diferença.",
    "pendencia",
    "remuneracao",
    "sim",
  ),

  // ────────────────────────────────────────────────────────────────────────
  // Segurado especial (rural)
  // ────────────────────────────────────────────────────────────────────────
  "PSE-POS": I(
    "PSE-POS",
    "Período de segurado especial positivo (não ratificado)",
    "Migrado de CAFIR/RGP com indício positivo, mas ainda pendente de ratificação — exige autodeclaração/análise.",
    "pendencia",
    "vinculo",
    "condicional",
    true,
  ),
  "PSE-PEN": I(
    "PSE-PEN",
    "Período de segurado especial pendente",
    "Pendente de análise/ratificação.",
    "pendencia",
    "vinculo",
    "sim",
    true,
  ),
  "PSE-NEG": I(
    "PSE-NEG",
    "Período de segurado especial negativo",
    "Indício negativo na análise; exige comprovação robusta da atividade rural.",
    "pendencia",
    "vinculo",
    "sim",
    true,
  ),
  "ISE-CVU": I(
    "ISE-CVU",
    "Período de segurado especial concomitante com outro período urbano",
    "O período rural não é computado automaticamente enquanto houver a concomitância.",
    "alerta",
    "vinculo",
    "condicional",
    true,
  ),

  // ────────────────────────────────────────────────────────────────────────
  // Processos trabalhistas / eSocial S-2500
  // ────────────────────────────────────────────────────────────────────────
  IDT: I(
    "IDT",
    "Indicador de Demanda de Natureza Trabalhista",
    "Vínculo/remuneração com origem em reclamatória trabalhista (GFIP 650). Exige atenção à comprovação do período.",
    "alerta",
    "vinculo",
    "condicional",
    true,
  ),
  "IVIN-PROC-TRAB": I(
    "IVIN-PROC-TRAB",
    "Vínculo possui processo trabalhista",
    "Processo trabalhista sem alteração de datas — informativo.",
    "alerta",
    "vinculo",
    "nao",
    true,
  ),
  "PVIN-REC-PROC-TRAB": I(
    "PVIN-REC-PROC-TRAB",
    "Reconhecimento de vínculo oriundo de processo trabalhista",
    "Vínculo criado por sentença (eSocial S-2500); exige comprovação (arts. 172 ss. da IN 128/2022).",
    "pendencia",
    "vinculo",
    "condicional",
    true,
  ),
  "PVIN-ADMISSAO-PROC-TRAB": I(
    "PVIN-ADMISSAO-PROC-TRAB",
    "Alteração de data de admissão oriunda de processo trabalhista",
    "Exige comprovação. Variantes: PVIN-DESLIG-PROC-TRAB, PVIN-ADMISSAO-DESLIG-PROC-TRAB.",
    "pendencia",
    "vinculo",
    "condicional",
  ),
  "IREM-VINC-PROC-TRAB": I(
    "IREM-VINC-PROC-TRAB",
    "Remuneração no vínculo oriunda de processo trabalhista (concomitante com remuneração normal)",
    "Liberada automaticamente, sem tratamento. Substituiu o IREM-RECL-TRAB (08/2024).",
    "alerta",
    "remuneracao",
    "nao",
    true,
  ),
  "PREM-VINC-PROC-TRAB": I(
    "PREM-VINC-PROC-TRAB",
    "Remuneração no vínculo oriunda de processo trabalhista (verba sozinha na competência)",
    "Exige comprovação da filiação no período.",
    "pendencia",
    "remuneracao",
    "condicional",
    true,
  ),
  "PVIN-TRAB-INTERM": I(
    "PVIN-TRAB-INTERM",
    "Vínculo possui informações de trabalho intermitente",
    "Alerta de tratamento (desde 05/2025 tratável direto no PRISMA).",
    "pendencia",
    "vinculo",
    "condicional",
    true,
  ),
  "IVIN-JORN-DIFERENCIADA": I(
    "IVIN-JORN-DIFERENCIADA",
    "Vínculo possui regime de jornada diferenciada (menos de 44h semanais)",
    "Meramente informativo.",
    "alerta",
    "vinculo",
    "nao",
    true,
  ),
  "IVIN-POSSUI-REM-TRANS": I(
    "IVIN-POSSUI-REM-TRANS",
    "Vínculo possui remuneração transferida (trabalhador cedido ou dirigente sindical)",
    "Informativo.",
    "alerta",
    "vinculo",
    "nao",
    true,
  ),

  // ────────────────────────────────────────────────────────────────────────
  // Remuneração — parcelas informativas
  // ────────────────────────────────────────────────────────────────────────
  "IREM-ACD": I(
    "IREM-ACD",
    "Remuneração possui parcela de Acordo, Convenção ou Dissídio Coletivo",
    "Não depende de comprovação; o valor já está somado à remuneração normal.",
    "alerta",
    "remuneracao",
    "nao",
    true,
  ),
  "IREM-ACD-DISS": I(
    "IREM-ACD-DISS",
    "Remuneração possui parcela de Dissídio Coletivo (variante antiga do IREM-ACD)",
    "Grafia usada em extratos mais antigos; mesmo significado prático do IREM-ACD.",
    "alerta",
    "remuneracao",
    "nao",
    true,
  ),
  "IREM-PARC-CEDIDO": I(
    "IREM-PARC-CEDIDO",
    "Parcela de remuneração de trabalhador cedido",
    "Informativo: parte da remuneração vem do cessionário. Variante: IREM-PARC-DIR-SIND (dirigente sindical).",
    "alerta",
    "remuneracao",
    "nao",
    true,
  ),
  "PREM-BLOQ-EC103": I(
    "PREM-BLOQ-EC103",
    "Pendência de bloqueio de remuneração/contribuição para ajuste entre competências (EC 103/2019)",
    "Competência bloqueada para os ajustes da EC 103 (vínculo extemporâneo, LC 123 concomitante sem complementação, inconsistência de PJ etc.). Mutuamente exclusivo com PSC-MEN-SM-EC103.",
    "pendencia",
    "remuneracao",
    "condicional",
    true,
  ),
  "PDESFAZ-AJ-EC103": I(
    "PDESFAZ-AJ-EC103",
    "Pendência por desfazimento de agrupamento ou utilização (EC 103/2019)",
    "Um ajuste da EC 103 foi desfeito; bloqueia novas operações de utilização/agrupamento no mesmo ano civil.",
    "pendencia",
    "remuneracao",
    "condicional",
    true,
  ),
  "PREM-FORA-ATIV-INTERM": I(
    "PREM-FORA-ATIV-INTERM",
    "Remuneração de trabalho intermitente fora do período de atividade",
    "O empregador não informou a convocatória/dias trabalhados; corrigir no eSocial.",
    "pendencia",
    "remuneracao",
    "condicional",
    true,
  ),
  "IREM-13": I(
    "IREM-13",
    "(não é indicador oficial)",
    'O 13º salário aparece no extrato como competência própria "13/AAAA" (gratificação natalina) na tabela de remunerações, não como indicador.',
    "alerta",
    "remuneracao",
    "nao",
  ),

  // ────────────────────────────────────────────────────────────────────────
  // Acertos (resultado de requerimentos)
  // ────────────────────────────────────────────────────────────────────────
  "AVRC-DEF": I(
    "AVRC-DEF",
    "Acerto de vínculos e remunerações confirmado pelo INSS",
    "Requerimento de acerto (VRE) deferido — o dado passou a valer. Variantes: AVRC-DEFJ (judicial), AVRC-DEFR (recursal); AVRC-IND/INDJ/INDR = indeferido.",
    "acerto",
    "vinculo",
    "nao",
    true,
  ),
  "AVRC-IND": I(
    "AVRC-IND",
    "Acerto de vínculos e remunerações indeferido pelo INSS",
    "Requerimento negado; o período continua sem valer.",
    "acerto",
    "vinculo",
    "sim",
  ),
  "AEXT-VT": I(
    "AEXT-VT",
    "Vínculo extemporâneo confirmado totalmente pelo INSS",
    "O PEXT foi tratado e o vínculo vale integralmente. Variantes: AEXT-VTJ (judicial), AEXT-VTR (recursal); AEXT-VP/VPT/VPR = confirmado parcialmente.",
    "acerto",
    "vinculo",
    "nao",
    true,
  ),
  "AEXT-IND": I(
    "AEXT-IND",
    "Vínculo extemporâneo não confirmado pelo INSS",
    "Comprovação da extemporaneidade indeferida; o período não conta. Em legendas antigas aparece como AEXT-VI.",
    "acerto",
    "vinculo",
    "sim",
  ),
  ACNISVR: I(
    "ACNISVR",
    "Acerto realizado pelo INSS (sistema CNIS-VR, descontinuado)",
    "Acerto histórico positivo feito pelo INSS.",
    "acerto",
    "vinculo",
    "nao",
    true,
  ),
  "ASE-DEF": I(
    "ASE-DEF",
    "Acerto de período de segurado especial deferido",
    "Atividade rural reconhecida. Variantes: ASE-DEFJ (judicial), ASE-DEFR (recursal); ASE-IND/INDR = indeferido; ASE-RPOS/RNEG = ratificado positivo/negativo.",
    "acerto",
    "vinculo",
    "nao",
    true,
  ),
  "ASE-IND": I(
    "ASE-IND",
    "Acerto de período de segurado especial indeferido",
    "Atividade rural não reconhecida administrativamente.",
    "acerto",
    "vinculo",
    "sim",
    true,
  ),
  "ADIV-DADOS-GFIP": I(
    "ADIV-DADOS-GFIP",
    "Validação de vínculo/remuneração com divergência de dado cadastral em GFIP",
    "Resolve a pendência PDIV-DADOS-GFIP (nome/NIT divergentes na GFIP).",
    "acerto",
    "vinculo",
    "nao",
  ),
  "PDIV-DADOS-GFIP": I(
    "PDIV-DADOS-GFIP",
    "Vínculo/remuneração pendente por divergência de dado cadastral do trabalhador em GFIP",
    "Não considerado até comprovar a titularidade (acerto ADIV-DADOS-GFIP).",
    "pendencia",
    "ambos",
    "sim",
  ),

  // ────────────────────────────────────────────────────────────────────────
  // NIT / cadastro
  // ────────────────────────────────────────────────────────────────────────
  "PNIT-CRIT": I(
    "PNIT-CRIT",
    "NIT em faixa crítica (mesmo NIT para mais de uma pessoa)",
    "Pendência cadastral.",
    "cadastro",
    "vinculo",
    "condicional",
  ),
  "PNIT-IND": I(
    "PNIT-IND",
    "NIT indeterminado (sem dados cadastrais)",
    "Pendência cadastral.",
    "cadastro",
    "vinculo",
    "condicional",
  ),
  "PNIT-SUP": I(
    "PNIT-SUP",
    "NIT com indício de superposição de dados",
    "Pendência cadastral (migração CADPF 2002-2004).",
    "cadastro",
    "vinculo",
    "condicional",
  ),

  // ────────────────────────────────────────────────────────────────────────
  // Legados / legendas antigas (podem aparecer em extratos antigos)
  // ────────────────────────────────────────────────────────────────────────
  "PREC-LC123-ANT": I(
    "PREC-LC123-ANT",
    "Recolhimento com código da LC 123 anterior à competência 04/2007",
    "Código do plano simplificado usado antes da vigência do plano — pendência (legenda antiga; fora do Anexo V atual).",
    "pendencia",
    "remuneracao",
    "sim",
  ),
  "IREC-CIRURAL": I(
    "IREC-CIRURAL",
    "Recolhimento com código de contribuinte individual rural sem homologação",
    "Legenda antiga; hoje o caso é tratado via PREC-CSE.",
    "alerta",
    "remuneracao",
    "condicional",
  ),
  "IGFIP-INF": I(
    "IGFIP-INF",
    "Indicador de GFIP meramente informativa",
    'Legenda antiga; a versão atual usa o indicador "GFIP".',
    "alerta",
    "remuneracao",
    "nao",
  ),
  "PVIN-OBITO": I(
    "PVIN-OBITO",
    "Data de admissão posterior ao óbito (extinto em 10/2024)",
    "Substituído por PVIN-ADM-OBITO e PVIN-DESLIG-OBITO.",
    "pendencia",
    "vinculo",
    "sim",
  ),
};

/**
 * Sinônimos e códigos antigos → código canônico da tabela acima.
 * Extratos emitidos antes das mudanças de nomenclatura ainda trazem os antigos.
 */
export const CNIS_INDICADORES_ALIASES: Record<string, string> = {
  "AEXT-VI": "AEXT-IND", // legenda antiga
  "IREM-RECL-TRAB": "IREM-VINC-PROC-TRAB", // extinto 08/2024
  "PREM-POS-QUARENTENA": "PREM-FVIN", // remuneração pós-quarentena: mesmo efeito prático (não computada)
  "PREM-POSQRT": "PREM-FVIN", // extinto 08/2024, substituído por PREM-POS-QUARENTENA
  ILEI123: "IREC-LC123", // nomenclatura PRISMA/SABI: IRECOL (ILEI123)
  IMEI: "IREC-MEI", // nomenclatura PRISMA/SABI: IRECOL (IMEI)
  ISALMIN: "IREC-LIM-SM",
  "IUTILIZ-EXC-MN-SM-EC103": "IUTILIZ-EXC-EC103",
};
