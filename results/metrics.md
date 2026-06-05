# Resultados Quantitativos — Grupo G9 (Observabilidade e Tracing)

> Gerado por `app/collect_metrics.py` em 2026-06-05 01:50 UTC.
> Contagens estruturais (spans, LLM, tools, erros, passos) são **exatas**; tokens, custo e latência são **estimativas** (LLM mockado).

## Tabela 1 — Telemetria capturada por cenário

| Cenário | Spans | Chamadas LLM | Execuções de Tools | Erros capturados | Passos do grafo | Status final |
|---|:--:|:--:|:--:|:--:|:--:|---|
| Execução Bem-Sucedida | 6 | 3 | 2 | 0 | 5 | Sucesso |
| Falha Controlada na Tool | 4 | 2 | 1 | 1 | 3 | Erro tratado |
| Loop Repetitivo (Estouro de Recursão) | 6 | 3 | 2 | 0 | 5 | GraphRecursionError (abortado) |

## Tabela 2 — Tokens, custo e latência estimados (GPT-4o-mini)

| Cenário | Tokens entrada | Tokens saída | Tokens total | Custo (USD) | Custo (BRL) | Latência est. (ms) |
|---|:--:|:--:|:--:|:--:|:--:|:--:|
| sucesso | 784 | 163 | 947 | $0.000215 | R$ 0.00116 | 2155 |
| falha | 454 | 72 | 526 | $0.000111 | R$ 0.00060 | 1405 |
| loop | 762 | 105 | 867 | $0.000177 | R$ 0.00096 | 2120 |
| **TOTAL** | **2000** | **340** | **2340** | **$0.000503** | **R$ 0.00272** | **5680** |

## Premissas das estimativas

- Tokenização: heurística de ~4 caracteres por token sobre o conteúdo real das mensagens.
- Overhead de schemas das ferramentas: 180 tokens por chamada de LLM.
- Preços GPT-4o-mini: US$ 0.15/1M tokens (entrada) e US$ 0.6/1M tokens (saída).
- Latência (perfil de produção): LLM 620 ms; tool de BD 130 ms; tool de API 165 ms.
- Câmbio de referência: US$ 1,00 = R$ 5.40.

Modelo de spans: `1 (raiz do workflow) + 1 por chamada de LLM + 1 por execução de tool`.
