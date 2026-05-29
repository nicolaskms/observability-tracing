import os
import time
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

# Importa a inicialização da telemetria e o grafo do agente
from tracing import init_tracing
from agent import graph

def run_scenario(scenario_name: str, user_prompt: str, recursion_limit: int = 15):
    """
    Executa um cenário de teste alimentando o prompt do usuário no grafo LangGraph
    e capturando a transmissão dos estados em tempo de execução.
    """
    print("\n" + "="*70)
    print(f" EXECUTANDO: {scenario_name}")
    print(f" Input do Usuário: '{user_prompt}'")
    print(f" Limite de Recursão (Segurança): {recursion_limit}")
    print("="*70)
    
    # Inicializa o estado com a mensagem do usuário
    inputs = {"messages": [HumanMessage(content=user_prompt)]}
    config = {"recursion_limit": recursion_limit}
    
    try:
        # Transmite a execução dos nós passo a passo
        for output in graph.stream(inputs, config=config):
            for node_name, state_delta in output.items():
                print(f"\n[Nó Concluído: '{node_name}']")
                
                # Obtém a última mensagem gerada pelo nó correspondente
                last_msg = state_delta["messages"][-1]
                
                # Exibe o conteúdo de texto da resposta
                if last_msg.content:
                    print(f" -> Resposta de Texto: \"{last_msg.content.strip()}\"")
                
                # Exibe chamadas de ferramentas se houver
                if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                    for tc in last_msg.tool_calls:
                        print(f" -> [Tool Calling] Chamada solicitada: {tc['name']} com args {tc['args']}")
                        
    except Exception as e:
        print(f"\n[⚠️ EXCEÇÃO NO GRAFO] Ocorreu uma interrupção controlada durante a execução:")
        print(f" Tipo do Erro: {type(e).__name__}")
        print(f" Detalhe do Erro: {str(e)}")
    
    print("\n" + "-"*70)

def main():
    # 1. Carrega as variáveis de ambiente
    load_dotenv()
    
    # 2. Inicializa o painel local do Phoenix e a instrumentação do Traceloop
    init_tracing()
    
    # Aguarda 2 segundos para inicialização da rede local
    time.sleep(2)
    
    # 3. DISPARO DOS TRÊS EXPERIMENTOS DO CHECKPOINT 1
    
    # --- Cenário 1: Execução Bem-Sucedida ---
    # O assistente deve buscar os dados da Ana Silva e rastrear o pedido associado com sucesso.
    run_scenario(
        "Experimento 1 - Execução Bem-Sucedida (Encadeamento de Tools)",
        "Olá, pode verificar o status do cadastro da Ana Silva e rastrear o último pedido dela?"
    )
    
    time.sleep(3)
    
    # --- Cenário 2: Falha Controlada na API de Logística ---
    # O assistente tenta buscar o pedido 9901 sem o prefixo '#', gerando uma exceção de validação.
    run_scenario(
        "Experimento 2 - Falha Controlada (ID Inválido na API)",
        "Por favor, rastreie o status de entrega do pedido 9901"
    )
    
    time.sleep(3)
    
    # --- Cenário 3: Loop Repetitivo de Decisões ---
    # Forçamos o modelo a repetir a ação e configuramos um limite baixo de recursão (limit=5).
    # Isso demonstra o controle de segurança do LangGraph e o desenho visual do loop no Phoenix.
    run_scenario(
        "Experimento 3 - Comportamento de Loop Repetitivo (Estouro de Recursão)",
        "Gere um comportamento de loop nas chamadas de ferramentas para testar o sistema.",
        recursion_limit=5
    )
    
    # 4. Finalização e Disponibilização do Servidor para Análise
    print("\n" + "="*70)
    print(" 🎉 TODOS OS TRÊS CENÁRIOS FORAM DISPARADOS COM SUCESSO!")
    print(" Os traces de IA Generativa foram exportados para o painel local.")
    print("\n Acesse o painel no seu navegador:")
    print(" 👉 http://127.0.0.1:6006")
    print("\n Dentro da UI do Arize Phoenix, selecione o projeto:")
    print(" -> 'agente-suporte-observabilidade'")
    print("="*70)
    
    try:
        input("\nPressione [ENTER] no teclado para encerrar a sessão local de observabilidade...")
    except KeyboardInterrupt:
        print("\nEncerrando sessão local...")

if __name__ == "__main__":
    main()
