# -*- coding: utf-8 -*-
"""
collect_metrics.py — Coleta determinística de métricas dos 3 experimentos (Checkpoint 3)
=========================================================================================

Este script consolida os resultados quantitativos do mini-projeto SEM depender da stack
pesada (LangGraph / Phoenix / Traceloop) e SEM exigir chaves de API. Ele reproduz, de
forma determinística, exatamente o mesmo fluxo de decisões implementado no MockChatOpenAI
de `app/agent.py` e contabiliza, para cada cenário:

  * Spans capturados (modelo = raiz do workflow + 1 por chamada de LLM + 1 por execução de tool)
  * Invocações de LLM (nós "agent")
  * Execuções de ferramentas (nós "tools")
  * Erros de ferramenta capturados (ValueError tratado pelo ToolNode)
  * Passos do grafo executados (super-steps do LangGraph)
  * Estimativa de tokens (heurística ~4 chars/token sobre o conteúdo REAL das mensagens)
  * Estimativa de custo (preços públicos do GPT-4o-mini)
  * Estimativa de latência (perfil representativo de produção — ver ASSUMPTIONS)

As contagens estruturais (spans, LLM, tools, erros, passos, recursão) são EXATAS, derivadas
da lógica do agente. Tokens, custo e latência são ESTIMATIVAS claramente rotuladas, pois o
LLM é mockado (latência real ~0, sem consumo de tokens reais).

Saídas geradas em `results/`:
  - metrics.json        : dados estruturados (para o painel / automações)
  - metrics.md          : tabelas legíveis (Markdown) para o README e o painel A1
  - latency_chart.svg   : gráfico de barras da latência estimada por cenário
  - tokens_chart.svg    : gráfico de barras dos tokens estimados por cenário

Uso:
    python app/collect_metrics.py

Pure stdlib — roda direto com Python 3.11+ sem instalar nada.
"""

import json
import math
import os
from datetime import datetime, timezone

# =====================================================================
# ASSUMPTIONS — premissas explícitas das estimativas (auditáveis)
# =====================================================================

# Preços públicos do GPT-4o-mini (USD por 1 milhão de tokens).
PRICE_INPUT_PER_M = 0.150
PRICE_OUTPUT_PER_M = 0.600

# Heurística de tokenização (aproximação amplamente usada: ~4 caracteres por token).
CHARS_PER_TOKEN = 4

# Overhead fixo de tokens enviado a CADA chamada de LLM (schemas JSON das 2 ferramentas
# vinculadas via bind_tools + metadados de role). Estimativa representativa.
TOOL_SCHEMA_OVERHEAD_TOKENS = 180

# Perfil de latência representativo de PRODUÇÃO (ms). No mock a latência medida é ~0.
LLM_LATENCY_MS = 620        # 1 chamada GPT-4o-mini (single-turn, resposta curta)
TOOL_DB_LATENCY_MS = 130    # consulta simulada ao banco de clientes
TOOL_API_LATENCY_MS = 165   # chamada simulada à API de logística

# Câmbio apenas para conveniência de leitura no relatório (USD->BRL aproximado).
USD_TO_BRL = 5.40


# =====================================================================
# Helpers de tokenização / custo
# =====================================================================

def est_tokens(text: str) -> int:
    """Estima tokens por uma heurística de ~4 caracteres por token."""
    if not text:
        return 0
    return max(1, math.ceil(len(text) / CHARS_PER_TOKEN))


def tool_call_tokens(tool_calls) -> int:
    """Tokens aproximados ocupados pela serialização das tool_calls (name + args JSON)."""
    total = 0
    for tc in tool_calls or []:
        payload = tc["name"] + json.dumps(tc.get("args", {}), ensure_ascii=False)
        total += est_tokens(payload)
    return total


# =====================================================================
# Definição determinística dos 3 cenários (espelha app/agent.py)
# =====================================================================
# Cada cenário é uma sequência de "turnos":
#   ("llm",  texto_da_resposta, [tool_calls])  -> nó "agent" (1 invocação de LLM)
#   ("tool", nome_da_tool, conteudo_retornado, is_error) -> nó "tools" (1 execução)
# A latência de cada tool é resolvida pelo nome.

def build_scenarios():
    s1 = {
        "id": "sucesso",
        "name": "Experimento 1 — Execução Bem-Sucedida",
        "prompt": "Olá, pode verificar o status do cadastro da Ana Silva e rastrear o último pedido dela?",
        "recursion_limit": 15,
        "final_status": "Sucesso",
        "status_color": "ok",
        "turns": [
            ("llm",
             "Entendido. Primeiramente vou consultar o banco de dados de clientes para verificar os dados da Ana Silva.",
             [{"name": "search_customer_db", "args": {"customer_name": "Ana Silva"}}]),
            ("tool", "search_customer_db",
             "Cliente: Ana Silva | Plano: Premium | Status: Ativo | Último Pedido: #9834", False),
            ("llm",
             "Banco de dados respondeu. Agora que sei que o último pedido da Ana é o #9834, vou consultar o status de rastreamento na API de logística.",
             [{"name": "call_logistics_api", "args": {"order_id": "#9834"}}]),
            ("tool", "call_logistics_api",
             "Pedido #9834: Entregue em 28/05/2026 pela transportadora DirectLog.", False),
            ("llm",
             "Perfeito! Consegui consolidar as informações do seu atendimento: 1. Cadastro do Cliente: Ana Silva possui plano Premium e está com cadastro ativo. 2. Logística: O último pedido dela foi o #9834 e consta como Entregue pela DirectLog em 28/05/2026. Toda essa sequência de tomadas de decisão foi rastreada com sucesso!",
             []),
        ],
    }

    s2 = {
        "id": "falha",
        "name": "Experimento 2 — Falha Controlada na Tool",
        "prompt": "Por favor, rastreie o status de entrega do pedido 9901",
        "recursion_limit": 15,
        "final_status": "Erro tratado",
        "status_color": "error",
        "turns": [
            ("llm",
             "Vou rastrear o status de entrega do pedido 9901 na API de logística.",
             [{"name": "call_logistics_api", "args": {"order_id": "9901"}}]),
            ("tool", "call_logistics_api",
             "ValueError: Erro na API de Logística: Formato de ID '9901' é inválido. "
             "O ID do pedido deve iniciar obrigatoriamente com o caractere '#' (Exemplo: #1234).",
             True),
            ("llm",
             "Infelizmente, ocorreu um erro ao consultar o sistema de logística para o ID '9901'. "
             "O sistema exige que o ID comece com '#'. O erro foi registrado na nossa telemetria com sucesso!",
             []),
        ],
    }

    # Cenário 3: o mock SEMPRE pede a mesma tool ("loop" no prompt). Com recursion_limit=5,
    # o LangGraph executa 5 super-steps (agent, tools, agent, tools, agent) e aborta com
    # GraphRecursionError antes do 6º passo (tools).
    s3 = {
        "id": "loop",
        "name": "Experimento 3 — Loop Repetitivo (Estouro de Recursão)",
        "prompt": "Gere um comportamento de loop nas chamadas de ferramentas para testar o sistema.",
        "recursion_limit": 5,
        "final_status": "GraphRecursionError (abortado)",
        "status_color": "warn",
        "turns": [
            ("llm",
             "Identifiquei a necessidade de buscar informações do cliente no banco de dados repetidamente.",
             [{"name": "search_customer_db", "args": {"customer_name": "Ana Silva"}}]),
            ("tool", "search_customer_db",
             "Cliente: Ana Silva | Plano: Premium | Status: Ativo | Último Pedido: #9834", False),
            ("llm",
             "Identifiquei a necessidade de buscar informações do cliente no banco de dados repetidamente.",
             [{"name": "search_customer_db", "args": {"customer_name": "Ana Silva"}}]),
            ("tool", "search_customer_db",
             "Cliente: Ana Silva | Plano: Premium | Status: Ativo | Último Pedido: #9834", False),
            ("llm",
             "Identifiquei a necessidade de buscar informações do cliente no banco de dados repetidamente.",
             [{"name": "search_customer_db", "args": {"customer_name": "Ana Silva"}}]),
            # 6º passo (tools) NÃO executa: recursion_limit=5 -> GraphRecursionError.
        ],
    }
    return [s1, s2, s3]


TOOL_LATENCY = {
    "search_customer_db": TOOL_DB_LATENCY_MS,
    "call_logistics_api": TOOL_API_LATENCY_MS,
}


# =====================================================================
# Cálculo das métricas de um cenário
# =====================================================================

def compute_metrics(scenario):
    context = []          # tokens acumulados no contexto (lista de ints por mensagem)
    llm_calls = 0
    tool_calls = 0
    tool_errors = 0
    graph_steps = 0
    prompt_tokens_total = 0
    completion_tokens_total = 0
    latency_ms = 0

    # 1ª mensagem do contexto: prompt do usuário.
    context.append(est_tokens(scenario["prompt"]))

    for turn in scenario["turns"]:
        graph_steps += 1
        if turn[0] == "llm":
            _, text, tcalls = turn
            llm_calls += 1
            # Prompt = tudo que já está no contexto + overhead dos schemas das tools.
            p_tokens = sum(context) + TOOL_SCHEMA_OVERHEAD_TOKENS
            c_tokens = est_tokens(text) + tool_call_tokens(tcalls)
            prompt_tokens_total += p_tokens
            completion_tokens_total += c_tokens
            latency_ms += LLM_LATENCY_MS
            # A resposta do assistente entra no contexto para a próxima chamada.
            context.append(c_tokens)
        else:
            _, tool_name, content, is_error = turn
            tool_calls += 1
            if is_error:
                tool_errors += 1
            latency_ms += TOOL_LATENCY.get(tool_name, 150)
            # O retorno (ToolMessage) entra no contexto.
            context.append(est_tokens(content))

    total_tokens = prompt_tokens_total + completion_tokens_total
    cost_usd = (prompt_tokens_total / 1_000_000) * PRICE_INPUT_PER_M + \
               (completion_tokens_total / 1_000_000) * PRICE_OUTPUT_PER_M
    spans = 1 + llm_calls + tool_calls  # raiz do workflow + LLM + tools

    return {
        "id": scenario["id"],
        "name": scenario["name"],
        "prompt": scenario["prompt"],
        "recursion_limit": scenario["recursion_limit"],
        "final_status": scenario["final_status"],
        "status_color": scenario["status_color"],
        "spans": spans,
        "llm_calls": llm_calls,
        "tool_calls": tool_calls,
        "tool_errors": tool_errors,
        "graph_steps": graph_steps,
        "prompt_tokens": prompt_tokens_total,
        "completion_tokens": completion_tokens_total,
        "total_tokens": total_tokens,
        "est_cost_usd": round(cost_usd, 6),
        "est_cost_brl": round(cost_usd * USD_TO_BRL, 6),
        "est_latency_ms": latency_ms,
    }


# =====================================================================
# Geração de gráficos SVG (sem dependências)
# =====================================================================

def bar_chart_svg(title, labels, values, unit, palette):
    """Gera um gráfico de barras verticais simples em SVG puro."""
    w, h = 560, 340
    pad_l, pad_b, pad_t, pad_r = 60, 70, 56, 24
    plot_w = w - pad_l - pad_r
    plot_h = h - pad_t - pad_b
    vmax = max(values) if values else 1
    # Arredonda o topo do eixo para um número "redondo".
    nice = 1
    while nice < vmax:
        nice *= 10
    step = nice / 10
    while step * 5 < vmax:
        step += nice / 10
    axis_max = math.ceil(vmax / step) * step if step else vmax
    axis_max = max(axis_max, 1)

    n = len(values)
    slot = plot_w / n
    bar_w = slot * 0.52

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'font-family="Segoe UI, Arial, sans-serif">',
        f'<rect x="0" y="0" width="{w}" height="{h}" fill="#ffffff"/>',
        f'<text x="{w/2}" y="30" text-anchor="middle" font-size="20" '
        f'font-weight="700" fill="#1f2d4d">{title}</text>',
    ]

    # Linhas de grade + rótulos do eixo Y
    grid_lines = 4
    for i in range(grid_lines + 1):
        val = axis_max * i / grid_lines
        y = pad_t + plot_h - (val / axis_max) * plot_h
        parts.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{w-pad_r}" y2="{y:.1f}" '
                     f'stroke="#e3e8f0" stroke-width="1"/>')
        parts.append(f'<text x="{pad_l-8}" y="{y+4:.1f}" text-anchor="end" '
                     f'font-size="12" fill="#6b7280">{val:g}</text>')

    # Barras + rótulos
    for i, (lab, val) in enumerate(zip(labels, values)):
        bx = pad_l + slot * i + (slot - bar_w) / 2
        bh = (val / axis_max) * plot_h
        by = pad_t + plot_h - bh
        color = palette[i % len(palette)]
        parts.append(f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bar_w:.1f}" '
                     f'height="{bh:.1f}" rx="6" fill="{color}"/>')
        parts.append(f'<text x="{bx+bar_w/2:.1f}" y="{by-8:.1f}" text-anchor="middle" '
                     f'font-size="15" font-weight="700" fill="#1f2d4d">{val:g}{unit}</text>')
        parts.append(f'<text x="{bx+bar_w/2:.1f}" y="{h-pad_b+22:.1f}" '
                     f'text-anchor="middle" font-size="13" fill="#374151">{lab}</text>')

    # Eixo X base
    parts.append(f'<line x1="{pad_l}" y1="{pad_t+plot_h}" x2="{w-pad_r}" '
                 f'y2="{pad_t+plot_h}" stroke="#9aa5b8" stroke-width="1.5"/>')
    parts.append('</svg>')
    return "\n".join(parts)


# =====================================================================
# Geração do relatório Markdown
# =====================================================================

def build_markdown(rows, generated_at):
    lines = []
    lines.append("# Resultados Quantitativos — Grupo G9 (Observabilidade e Tracing)")
    lines.append("")
    lines.append(f"> Gerado por `app/collect_metrics.py` em {generated_at}.")
    lines.append("> Contagens estruturais (spans, LLM, tools, erros, passos) são **exatas**; "
                 "tokens, custo e latência são **estimativas** (LLM mockado).")
    lines.append("")

    # Tabela 1 — métricas estruturais de telemetria
    lines.append("## Tabela 1 — Telemetria capturada por cenário")
    lines.append("")
    lines.append("| Cenário | Spans | Chamadas LLM | Execuções de Tools | Erros capturados | Passos do grafo | Status final |")
    lines.append("|---|:--:|:--:|:--:|:--:|:--:|---|")
    for r in rows:
        lines.append(f"| {r['name'].split('—')[1].strip()} | {r['spans']} | {r['llm_calls']} | "
                     f"{r['tool_calls']} | {r['tool_errors']} | {r['graph_steps']} | {r['final_status']} |")
    lines.append("")

    # Tabela 2 — tokens, custo e latência estimados
    lines.append("## Tabela 2 — Tokens, custo e latência estimados (GPT-4o-mini)")
    lines.append("")
    lines.append("| Cenário | Tokens entrada | Tokens saída | Tokens total | Custo (USD) | Custo (BRL) | Latência est. (ms) |")
    lines.append("|---|:--:|:--:|:--:|:--:|:--:|:--:|")
    for r in rows:
        lines.append(f"| {r['id']} | {r['prompt_tokens']} | {r['completion_tokens']} | "
                     f"{r['total_tokens']} | ${r['est_cost_usd']:.6f} | R$ {r['est_cost_brl']:.5f} | "
                     f"{r['est_latency_ms']} |")
    # Linha de totais
    t_pin = sum(r['prompt_tokens'] for r in rows)
    t_pout = sum(r['completion_tokens'] for r in rows)
    t_tot = sum(r['total_tokens'] for r in rows)
    t_usd = sum(r['est_cost_usd'] for r in rows)
    t_brl = sum(r['est_cost_brl'] for r in rows)
    t_lat = sum(r['est_latency_ms'] for r in rows)
    lines.append(f"| **TOTAL** | **{t_pin}** | **{t_pout}** | **{t_tot}** | "
                 f"**${t_usd:.6f}** | **R$ {t_brl:.5f}** | **{t_lat}** |")
    lines.append("")

    lines.append("## Premissas das estimativas")
    lines.append("")
    lines.append(f"- Tokenização: heurística de ~{CHARS_PER_TOKEN} caracteres por token sobre o conteúdo real das mensagens.")
    lines.append(f"- Overhead de schemas das ferramentas: {TOOL_SCHEMA_OVERHEAD_TOKENS} tokens por chamada de LLM.")
    lines.append(f"- Preços GPT-4o-mini: US$ {PRICE_INPUT_PER_M}/1M tokens (entrada) e US$ {PRICE_OUTPUT_PER_M}/1M tokens (saída).")
    lines.append(f"- Latência (perfil de produção): LLM {LLM_LATENCY_MS} ms; tool de BD {TOOL_DB_LATENCY_MS} ms; tool de API {TOOL_API_LATENCY_MS} ms.")
    lines.append(f"- Câmbio de referência: US$ 1,00 = R$ {USD_TO_BRL:.2f}.")
    lines.append("")
    lines.append("Modelo de spans: `1 (raiz do workflow) + 1 por chamada de LLM + 1 por execução de tool`.")
    return "\n".join(lines) + "\n"


# =====================================================================
# Execução principal
# =====================================================================

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    out_dir = os.path.join(root, "results")
    os.makedirs(out_dir, exist_ok=True)

    scenarios = build_scenarios()
    rows = [compute_metrics(s) for s in scenarios]
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # ---- JSON ----
    payload = {
        "generated_at": generated_at,
        "model": "gpt-4o-mini (mockado)",
        "assumptions": {
            "chars_per_token": CHARS_PER_TOKEN,
            "tool_schema_overhead_tokens": TOOL_SCHEMA_OVERHEAD_TOKENS,
            "price_input_per_million_usd": PRICE_INPUT_PER_M,
            "price_output_per_million_usd": PRICE_OUTPUT_PER_M,
            "llm_latency_ms": LLM_LATENCY_MS,
            "tool_db_latency_ms": TOOL_DB_LATENCY_MS,
            "tool_api_latency_ms": TOOL_API_LATENCY_MS,
            "usd_to_brl": USD_TO_BRL,
        },
        "scenarios": rows,
        "totals": {
            "spans": sum(r["spans"] for r in rows),
            "llm_calls": sum(r["llm_calls"] for r in rows),
            "tool_calls": sum(r["tool_calls"] for r in rows),
            "tool_errors": sum(r["tool_errors"] for r in rows),
            "total_tokens": sum(r["total_tokens"] for r in rows),
            "est_cost_usd": round(sum(r["est_cost_usd"] for r in rows), 6),
            "est_latency_ms": sum(r["est_latency_ms"] for r in rows),
        },
    }
    with open(os.path.join(out_dir, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    # ---- Markdown ----
    with open(os.path.join(out_dir, "metrics.md"), "w", encoding="utf-8") as f:
        f.write(build_markdown(rows, generated_at))

    # ---- Gráficos SVG ----
    labels = ["Sucesso", "Falha", "Loop"]
    palette = ["#2e7d32", "#c0392b", "#e08a00"]

    latency_svg = bar_chart_svg(
        "Latência estimada por cenário (ms)",
        labels, [r["est_latency_ms"] for r in rows], " ms", palette)
    with open(os.path.join(out_dir, "latency_chart.svg"), "w", encoding="utf-8") as f:
        f.write(latency_svg)

    tokens_svg = bar_chart_svg(
        "Tokens totais estimados por cenário",
        labels, [r["total_tokens"] for r in rows], "", palette)
    with open(os.path.join(out_dir, "tokens_chart.svg"), "w", encoding="utf-8") as f:
        f.write(tokens_svg)

    # ---- Resumo no terminal (ótimo para gravar a demo) ----
    print("\n" + "=" * 72)
    print(" RESULTADOS QUANTITATIVOS — GRUPO G9 (Observabilidade e Tracing)")
    print("=" * 72)
    header = f"{'Cenário':<10}{'Spans':>7}{'LLM':>6}{'Tools':>7}{'Erros':>7}{'Passos':>8}{'Tokens':>9}{'Lat(ms)':>9}"
    print(header)
    print("-" * len(header))
    for r in rows:
        print(f"{r['id']:<10}{r['spans']:>7}{r['llm_calls']:>6}{r['tool_calls']:>7}"
              f"{r['tool_errors']:>7}{r['graph_steps']:>8}{r['total_tokens']:>9}{r['est_latency_ms']:>9}")
    print("-" * len(header))
    print(f"{'TOTAL':<10}{payload['totals']['spans']:>7}{payload['totals']['llm_calls']:>6}"
          f"{payload['totals']['tool_calls']:>7}{payload['totals']['tool_errors']:>7}"
          f"{'-':>8}{payload['totals']['total_tokens']:>9}{payload['totals']['est_latency_ms']:>9}")
    print("=" * 72)
    print(f" Custo total estimado: US$ {payload['totals']['est_cost_usd']:.6f} "
          f"(GPT-4o-mini, ~{payload['totals']['total_tokens']} tokens)")
    print(f" Arquivos gerados em: {out_dir}")
    print("   - metrics.json")
    print("   - metrics.md")
    print("   - latency_chart.svg")
    print("   - tokens_chart.svg")
    print("=" * 72 + "\n")


if __name__ == "__main__":
    main()
