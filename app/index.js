/*
 * index.js — API Express com tracing
 * 
 * Rotas:
 *   GET /         → Health check simples
 *   GET /process  → Simula processamento com span manual customizado
 */

const express = require('express');
const { trace } = require('@opentelemetry/api');

const app = express();
const PORT = process.env.PORT || 3000;

// Obtém o tracer para criar spans manuais
const tracer = trace.getTracer('api-observability');

// =============================================
// Rota: GET /
// Retorna status da API (health check)
// O span é criado AUTOMATICAMENTE pela instrumentação do Express
// =============================================
app.get('/', (req, res) => {
  res.json({
    status: 'ok',
    message: 'API rodando com tracing!',
    timestamp: new Date().toISOString(),
  });
});

// =============================================
// Rota: GET /process
// Simula um processamento com spans manuais aninhados
// Demonstra a criação programática de spans filhos
// =============================================
app.get('/process', (req, res) => {
  // Cria um span manual DENTRO do span automático do Express
  // Isso aparece como span filho no Jaeger
  tracer.startActiveSpan('processamento-dados', (span) => {
    // Adiciona atributos ao span (metadados visíveis no Jaeger)
    span.setAttribute('processo.tipo', 'simulacao');
    span.setAttribute('processo.descricao', 'Simulação de processamento de dados');

    // Simula processamento assíncrono (500ms)
    setTimeout(() => {
      // Adiciona um evento ao span (log dentro do trace)
      span.addEvent('Processamento concluído', {
        'resultado.itens': 42,
        'resultado.status': 'sucesso',
      });

      // Finaliza o span manual
      span.end();

      res.json({
        status: 'ok',
        message: 'Processamento concluído com sucesso',
        dados: {
          itensProcessados: 42,
          tempoMs: 500,
        },
        timestamp: new Date().toISOString(),
      });
    }, 500);
  });
});

// Inicia o servidor
app.listen(PORT, () => {
  console.log(`[API] Servidor rodando em http://localhost:${PORT}`);
  console.log(`[API] Rotas disponíveis:`);
  console.log(`  GET /         → Health check`);
  console.log(`  GET /process  → Processamento com tracing`);
});
