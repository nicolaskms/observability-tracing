import os
from dotenv import load_dotenv
import phoenix as px
from traceloop.sdk import Traceloop

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

def init_tracing():
    """
    Inicializa o painel do Arize Phoenix localmente e acopla a telemetria 
    do Traceloop (OpenLLMetry) para capturar traces da execução do agente.
    """
    print("\n==================================================")
    print("[Tracing] Iniciando Arize Phoenix local...")
    
    host = os.getenv("PHOENIX_HOST", "127.0.0.1")
    port = int(os.getenv("PHOENIX_PORT", "6006"))
    
    # Inicia a UI e o coletor local do Arize Phoenix
    px.launch_app(host=host, port=port)
    
    print(f"[Tracing] Arize Phoenix rodando em http://{host}:{port}")
    print("[Tracing] Inicializando Traceloop (OpenLLMetry)...")
    
    # Inicializa o SDK de instrumentação apontando para o endpoint OTLP local do Phoenix
    traceloop_endpoint = os.getenv("TRACELOOP_BASE_URL", f"http://{host}:{port}/v1/traces")
    
    Traceloop.init(
        app_name="agente-suporte-observabilidade",
        disable_batch=True,                    # Desabilita lote para enviar traces imediatamente
        api_endpoint=traceloop_endpoint,       # Endpoint OTLP/HTTP exposto pelo Phoenix
        traceloop_sync_enabled=False           # Desabilita sincronização com plataforma cloud do Traceloop
    )
    
    print(f"[Tracing] Telemetria exportando para {traceloop_endpoint}")
    print("==================================================\n")
