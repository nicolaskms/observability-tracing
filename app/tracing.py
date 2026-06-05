import os
from dotenv import load_dotenv
import phoenix as px
from phoenix.otel import register
from openinference.instrumentation.langchain import LangChainInstrumentor

load_dotenv()


def init_tracing():
    """
    Sobe o Arize Phoenix localmente e registra o TracerProvider do OpenTelemetry
    apontando para o coletor interno do Phoenix. Em seguida, instrumenta o
    LangChain/LangGraph via callbacks (OpenInference), capturando automaticamente:
      - Chamadas ao modelo (nó "agent")
      - Execuções de ferramentas (nó "tools"), incluindo erros
      - Passos do grafo de estados do LangGraph
    """
    print("\n" + "=" * 50)
    print("[Tracing] Iniciando Arize Phoenix local...")

    host = os.getenv("PHOENIX_HOST", "127.0.0.1")
    port = int(os.getenv("PHOENIX_PORT", "6006"))

    # Usa variáveis de ambiente para evitar os avisos de deprecação
    os.environ.setdefault("PHOENIX_HOST", host)
    os.environ.setdefault("PHOENIX_PORT", str(port))

    px.launch_app()

    print(f"[Tracing] Arize Phoenix rodando em http://{host}:{port}")
    print("[Tracing] Registrando TracerProvider (OpenTelemetry -> Phoenix)...")

    # Registra o TracerProvider do OTel apontando para o coletor local do Phoenix
    tracer_provider = register(
        project_name="agente-suporte-observabilidade",
        endpoint=f"http://{host}:{port}/v1/traces",
        verbose=False,
    )

    # Instrumenta LangChain e LangGraph via o sistema de callbacks (captura qualquer BaseChatModel)
    LangChainInstrumentor().instrument(tracer_provider=tracer_provider)

    print(f"[Tracing] Instrumentação LangChain/LangGraph ativa")
    print(f"[Tracing] Telemetria -> http://{host}:{port}/v1/traces")
    print(f"[Tracing] Projeto: agente-suporte-observabilidade")
    print("=" * 50 + "\n")
