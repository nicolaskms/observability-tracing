# Painel A1 (Checkpoint 3) — Grupo G9

Draft do painel acadêmico em **A1 retrato (594 × 841 mm)**, no padrão de 6 blocos da disciplina.
O arquivo [`poster.html`](poster.html) é autocontido (HTML + CSS) e foi dimensionado para impressão.

## Exportar para PDF (versão quase-final)

1. Abra `poster.html` no **Google Chrome** ou **Microsoft Edge**.
2. Pressione **Ctrl + P** → em *Destino*, escolha **"Salvar como PDF"**.
3. Em **Mais configurações**:
   - **Tamanho do papel:** `A1` (se não houver, use *Personalizado* `594 × 841 mm`).
   - **Margens:** `Nenhuma`.
   - **Escala:** `Padrão` (100%).
   - Marque **"Gráficos de plano de fundo"** (para sair com as cores).
4. Clique em **Salvar**. O resultado é um PDF A1 de **uma página**, pronto para revisão e impressão.

> Dica: para conferir na tela, dê *zoom out* (Ctrl + `-`) — em A1 o painel é grande por natureza.

## O que já está no painel

| Bloco | Conteúdo |
|---|---|
| 01 Contexto & Motivação | Problema da opacidade ("caixa-preta") em agentes |
| 02 Conceitos-chave | Glossário: trace, span, tool calling, OTel semconv, OTLP |
| 03 Estado da arte | Tabela comparativa das ferramentas (OTel, OpenLLMetry, Phoenix, LangSmith, Langfuse) |
| 04 Arquitetura & método | Diagrama do grafo LangGraph + pipeline de telemetria |
| 05 Experimento & demo | 3 cenários, tabela de métricas reais, 2 gráficos, screenshots do Phoenix |
| 06 Discussão & limitações | O que funcionou / limitações / próximos passos |
| Rodapé | 8 referências IEEE + QR code do repositório |

Fonte do corpo **≥ 24 pt** e predominância de diagrama/tabela/gráfico sobre texto corrido,
conforme a rubrica.

## Antes de mandar para a gráfica — checklist

- [ ] Preencher os **nomes dos integrantes** no cabeçalho (`[Nome 1] … [Nome 4]`).
- [ ] Rodar `python app/collect_metrics.py` para atualizar os gráficos em `../results/`.
- [ ] Capturar os 2 **screenshots do Phoenix** e salvá-los em `../docs/`
      (`phoenix-sucesso.png` e `phoenix-erro.png`) — eles aparecem automaticamente no Bloco 05.
      Enquanto não existem, o painel mostra molduras-placeholder no lugar.
- [ ] (Opcional) Trocar o QR online por um PNG **offline** se for imprimir sem internet:
      substitua o `<img>` do rodapé por `<img src="assets/qr-repo.png">`.

## Imagens usadas pelo painel

| Caminho | Origem |
|---|---|
| `../results/tokens_chart.svg` | gerado por `app/collect_metrics.py` |
| `../results/latency_chart.svg` | gerado por `app/collect_metrics.py` |
| `../docs/phoenix-sucesso.png` | screenshot manual do Phoenix (cenário de sucesso) |
| `../docs/phoenix-erro.png` | screenshot manual do Phoenix (span de erro) |
| QR code | `api.qrserver.com` apontando para o repositório no GitHub |
