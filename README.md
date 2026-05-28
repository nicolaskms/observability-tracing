# Observability Tracing

## Objetivo
Demonstrar observabilidade e tracing com uma API simples.

## Backend (Express)
API Node.js com rotas basicas que retornam JSON.

### Rotas
- GET / -> { "status": "ok", "message": "API running" }
- GET /process?input=teste -> { "status": "processed", "input": "teste" }

### Como rodar
1. cd backend
2. npm install
3. npm start

Padrao: http://localhost:3000
