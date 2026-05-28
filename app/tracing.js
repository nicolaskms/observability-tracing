/*
 * tracing.js — Configuração do OpenTelemetry
 * 
 * Este arquivo DEVE ser carregado ANTES de qualquer outro módulo.
 * Uso: node --require ./tracing.js index.js
 * 
 * Responsável por:
 * - Inicializar o SDK do OpenTelemetry
 * - Configurar o exportador OTLP (gRPC) para o Jaeger
 * - Registrar instrumentações automáticas (HTTP + Express)
 * - Definir o nome do serviço que aparece no Jaeger
 */

require('dotenv').config();

const { NodeSDK } = require('@opentelemetry/sdk-node');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-grpc');
const { Resource } = require('@opentelemetry/resources');
const { ATTR_SERVICE_NAME } = require('@opentelemetry/semantic-conventions');
const { HttpInstrumentation } = require('@opentelemetry/instrumentation-http');
const { ExpressInstrumentation } = require('@opentelemetry/instrumentation-express');

// Nome do serviço que vai aparecer no Jaeger
const serviceName = process.env.OTEL_SERVICE_NAME || 'api-observability';

// Endpoint do coletor OTLP (Jaeger)
const otlpEndpoint = process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'http://localhost:4317';

// Configura o exportador OTLP via gRPC
const traceExporter = new OTLPTraceExporter({
  url: otlpEndpoint,
});

// Inicializa o SDK do OpenTelemetry
const sdk = new NodeSDK({
  // Define o recurso com o nome do serviço
  resource: new Resource({
    [ATTR_SERVICE_NAME]: serviceName,
  }),

  // Exportador de traces (envia para o Jaeger)
  traceExporter: traceExporter,

  // Instrumentações automáticas
  instrumentations: [
    // Captura automaticamente todas as requisições HTTP (entrada e saída)
    new HttpInstrumentation(),

    // Captura automaticamente rotas e middlewares do Express
    new ExpressInstrumentation(),
  ],
});

// Inicia o SDK
sdk.start();

console.log(`[Tracing] OpenTelemetry inicializado`);
console.log(`[Tracing] Serviço: ${serviceName}`);
console.log(`[Tracing] Exportando para: ${otlpEndpoint}`);

// Encerramento graceful — garante que os últimos spans sejam enviados
process.on('SIGTERM', () => {
  sdk
    .shutdown()
    .then(() => console.log('[Tracing] SDK encerrado com sucesso'))
    .catch((err) => console.error('[Tracing] Erro ao encerrar SDK:', err))
    .finally(() => process.exit(0));
});
