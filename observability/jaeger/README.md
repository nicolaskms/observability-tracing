# Observabilidade e Tracing em Agentes de IA

## Objetivo

Este projeto tem como objetivo demonstrar conceitos de observabilidade e tracing aplicados a uma arquitetura simples de agentes de IA.

Utilizamos **OpenTelemetry** para instrumentar uma API Node.js/Express e exportar traces para o **Jaeger**, permitindo visualizar o fluxo completo das requisições, identificar gargalos e entender o comportamento da aplicação em tempo real.

## Tecnologias utilizadas

- **Node.js** — Runtime da API
- **Express** — Framework HTTP
- **OpenTelemetry SDK** — Instrumentação e coleta de traces
- **Jaeger** — Visualização e análise de traces distribuídos
- **Docker / Docker Compose** — Orquestração dos serviços
- **OTLP (gRPC)** — Protocolo de exportação de telemetria

## Arquitetura

```
┌──────────────┐       OTLP/gRPC        ┌──────────────┐
│              │      (porta 4317)       │              │
│   API Node   │ ──────────────────────► │    Jaeger    │
│   (Express)  │                         │              │
│              │                         │   UI: 16686  │
└──────────────┘                         └──────────────┘
    porta 3000
```

**Fluxo:**
1. O cliente faz uma requisição HTTP para a API (porta 3000)
2. O OpenTelemetry captura automaticamente a requisição (instrumentação HTTP + Express)
3. Spans são criados para cada operação (incluindo spans manuais customizados)
4. Os traces são exportados via OTLP/gRPC para o Jaeger (porta 4317)
5. Os traces podem ser visualizados na UI do Jaeger (porta 16686)

## Estrutura do projeto

```
observability-tracing/
├── docker-compose.yml              # Orquestração dos serviços
├── observability/
│   └── jaeger/
│       └── README.md               # Este arquivo
└── app/
    ├── Dockerfile                   # Container da API
    ├── package.json                 # Dependências (Express + OpenTelemetry)
    ├── tracing.js                   # ★ Configuração do OpenTelemetry
    ├── index.js                     # API Express (rotas / e /process)
    └── .env                         # Variáveis de ambiente
```

## Configuração do Tracing (OpenTelemetry)

O arquivo `app/tracing.js` é o coração da instrumentação. Ele é carregado **antes** da aplicação usando `--require`:

```bash
node --require ./tracing.js index.js
```

### O que ele faz:

| Componente | Pacote | Função |
|------------|--------|--------|
| **SDK** | `@opentelemetry/sdk-node` | Orquestra toda a instrumentação |
| **Exportador** | `@opentelemetry/exporter-trace-otlp-grpc` | Envia traces para o Jaeger via gRPC |
| **HTTP Instrumentation** | `@opentelemetry/instrumentation-http` | Captura automaticamente requisições HTTP |
| **Express Instrumentation** | `@opentelemetry/instrumentation-express` | Captura rotas e middlewares do Express |
| **Resource** | `@opentelemetry/resources` | Define o nome do serviço (`api-observability`) |

### Rotas da API

| Rota | Método | Descrição | Tipo de Span |
|------|--------|-----------|--------------|
| `/` | GET | Health check — retorna status da API | Automático (HTTP + Express) |
| `/process` | GET | Simula processamento de dados (~500ms) | Automático + **Span manual** (`processamento-dados`) |

A rota `/process` demonstra a criação de **spans manuais customizados** com atributos e eventos, visíveis como spans filhos no Jaeger.

## Como executar

### Pré-requisitos

- Docker e Docker Compose instalados

### Subir os serviços

Na pasta principal do projeto, execute:

```bash
docker-compose up -d
```

### Testar a API

```bash
# Health check
curl http://localhost:3000/

# Processamento com tracing (gera span manual)
curl http://localhost:3000/process
```

### Visualizar os traces

1. Acesse o Jaeger: **http://localhost:16686**
2. No campo **Service**, selecione `api-observability`
3. Clique em **Find Traces**
4. Clique em um trace para ver os spans detalhados

## O que aparece no Jaeger

Ao chamar `GET /process`, o trace mostra a seguinte hierarquia de spans:

```
api-observability: GET /process              ← span automático (HTTP)
└── api-observability: GET /process          ← span automático (Express)
    └── api-observability: processamento-dados  ← span MANUAL com atributos
```

O span manual `processamento-dados` contém:
- **Atributos**: `processo.tipo`, `processo.descricao`
- **Eventos**: `Processamento concluído` com `resultado.itens` e `resultado.status`

## Integrantes e responsabilidades

| Parte | Responsável | Entrega |
|-------|-------------|---------|
| 1 — Infra/Docker | Pessoa 1 | `docker-compose.yml`, Jaeger rodando |
| 2 — Backend | Pessoa 2 | Projeto Node.js, Express, rotas |
| 3 — Tracing | Pessoa 3 | OpenTelemetry, exportação Jaeger, traces |
| 4 — Documentação | Pessoa 4 | README, arquitetura, prints |