# Backlog — dívidas do CNIS Parser

Levantado em 2026-08-11/12 por inspeção do repo + medição do serviço no H1.
A estratégia maior de ingestão de PDF (Docling, OCR, custos, capacidade do H1) vive em
[`prc_extensao_ingester/docs/PLANO.md`](https://github.com/ProcStudioOrg/prc_extensao_ingester/blob/main/docs/PLANO.md).

**Nada disto foi aplicado** — refatoração segurada por decisão do Bruno em 2026-08-11.
Este arquivo existe para que, no dia em que voltarmos, a informação medida não tenha
que ser levantada de novo.

Estado atual do serviço: 1 worker, ~1 parse/s serializado, zero observabilidade.
O H1 tem 8 vCPU / 32 GB e load 0,57 — **o servidor não é o gargalo, o app é.**

---

## P0 — meia hora, resolve ~90% do risco

### 1. As rotas bloqueiam o event loop

`app/routes/parse.py:64,71,78` — as três rotas são `async def` mas chamam
`_parse_and_respond()` (`:33`, síncrono) diretamente. O parse roda **dentro do event loop**,
então um upload congela o serviço inteiro, incluindo o `/health`.

Medido localmente, CNIS real de 17 páginas:

| Cenário | Tempo |
|---|---|
| parse isolado | 1,01 s |
| 3 parses concorrentes | 1,0 s / 2,0 s / 3,1 s (fila perfeita) |
| `/health` ocioso | 0,002 s |
| `/health` durante os 3 parses | **2,57 s** |

**Correção:** trocar `async def` → `def` nas três rotas. O FastAPI passa a despachar para o
threadpool sozinho. É literalmente apagar a palavra `async` em 3 linhas.

Ressalva: o parse é CPU-bound puro (regex), então o GIL continua limitando o *throughput*.
O threadpool resolve o congelamento do `/health`; quem resolve throughput é o item 2.

### 2. Um worker só

`deploy/setup.sh:130` — o `ExecStart` não passa `--workers`. Confirmado no servidor:
`systemctl show cnis_parser -p TasksCurrent` → `TasksCurrent=1`.

**Correção:** `--workers 4` no `ExecStart`. Com 8 vCPU compartilhados com legal_data,
Postgres ×2 e Redis, 4 é folgado. Junto com o item 1, sai de ~1 parse/s serializado para
~4 em paralelo.

### 3. O PDF é aberto duas vezes por request

`app/services/parser_service.py:34` abre o PDF só para ler a página 1 e checar a variante;
`cnis_parser_final.py:80` abre de novo para parsear. ~10–20% de desperdício por request.

**Correção:** abrir uma vez e passar o texto da primeira página (ou o objeto) adiante.

### 4. Sem rate limit em lugar nenhum

Nem `limit_req` no nginx, nem nada no app. Com serviço single-worker, uma chave vazada
derruba o serviço com trivialidade.

**Correção:** `limit_req_zone` + `limit_req` no snippet `/etc/nginx/snippets/cnis_parser.conf`
(gerado por `deploy/setup.sh`).

---

## P1 — a semana seguinte

### 5. Zero observabilidade

Diferente de legal_data, WAO e Signer, este serviço não grava `usage_events` nem manda
relatório diário para o dashboard. Para descobrir o volume foi preciso ler journald na mão —
e o último parse real de produção foi em **5 de agosto**, vindo de `54.234.88.122`
(ProcStudio na AWS).

**Correção:** seguir o padrão dos outros três serviços — `usage_events` local com
`ip_hash = SHA256(ip + USAGE_IP_SALT)` e envio às 00:05 America/Sao_Paulo para
`https://ffd.belzinhos.com.br/api/webhooks/usage?token=<WEBHOOK_SECRET>`, com heartbeat
mesmo zerado (ausência = serviço com problema).

Registrar por request: tempo, nº de vínculos, endpoint, código de erro.

### 6. Falha não é diagnosticável

`app/services/parser_service.py:73` — no `finally`, o tempfile é apagado sempre. Quando dá
`PARSE_ERROR` você recebe "Failed to parse" e **não tem como reproduzir**.

Para um parser heurístico ainda em evolução — os últimos 5 commits são todos correção de
parsing (indicadores, espécie 32, células quebradas) — isto é o que mais vai custar em
produção.

**Correção:** quarentena dos PDFs que falharam.

> ⚠️ **Definir a política de expurgo ANTES de ligar.** Quarentena de CNIS é armazenar CPF,
> NIT, nome da mãe e salários. Isto é dado pessoal sob LGPD e hoje o serviço não persiste
> nada (o que é uma virtude que estamos deliberadamente abrindo mão).

### 7. Sem timeout de parse

O nginx corta o cliente em 60 s (`deploy/setup.sh:179`), mas o worker continua preso. Um PDF
patológico segura um worker indefinidamente — hoje, o único worker.

**Correção:** teto de tempo por parse, com erro nomeado.

---

## P2 — dívidas menores

### 8. `CNIS_MAX_UPLOAD_SIZE_MB` é ignorado

`app/config.py:8` declara a config; `app/routes/parse.py:12` tem `MAX_SIZE` hardcoded em
16 MB e usa isso em `:26`. Mexer no `.env` não faz efeito nenhum — pior que não existir,
porque parece que funciona.

### 9. `pytest` não roda no venv local

O `.venv` tem só o `requirements_simple` instalado, então `tests/test_api.py` quebra no
import do FastAPI. Não é bug de produção, é atrito de quem for mexer.

**Correção:** `pip install -r requirements-dev.txt`, ou documentar no README.

### 10. `docker-compose.yml` é caminho morto

O deploy real é systemd + venv (`deploy/setup.sh` + GitHub Actions). O compose sugere um
caminho que ninguém usa — mesmo caso do config Kamal no `prc_wao`.

**Correção:** apagar, ou marcar como "somente desenvolvimento local" no topo do arquivo.

### 11. Comparação de API key não é constant-time

`app/auth.py:15` — `if api_key != settings.api_key`. Timing attack é teórico aqui (a rota
está atrás de nginx e a chave é longa), mas `secrets.compare_digest` é uma linha e é o que
o resto do ecossistema ProcStudio já faz (`secure_compare` no padrão DJEN).

---

## Fora de escopo (registrado para não voltar à discussão)

- **Não transformar este serviço em ingestor genérico de PDF.** Ele vale exatamente por ser
  determinístico e validado a 100% contra 39 CNIS. Ingestão genérica é outro problema, com
  outras SLAs e outro perfil de custo — e já tem casa própria em
  [`prc_extensao_ingester`](https://github.com/ProcStudioOrg/prc_extensao_ingester).
- **Não construir fila.** Com 4 workers a ~1,5 s/parse dá ~9 mil parses/hora. O volume real
  não chega perto disso.
- **Não adicionar OCR aqui.** CNIS do Meu INSS é nativo. CNIS escaneado é caso do ingester.
