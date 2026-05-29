import os
from typing import Any, List, Optional, Dict, Union, Annotated, Sequence
import operator
from typing_extensions import TypedDict

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, ToolMessage, ToolCall
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.runnables import Runnable
from langchain_core.tools import tool

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

# =====================================================================
# 1. Simulação do LLM (MockChatOpenAI)
#
# Criamos um modelo mock robusto que herda de BaseChatModel da LangChain.
# Isso garante que todas as chamadas gerem spans padrão da LangChain,
# que são capturados automaticamente pelo Traceloop/Phoenix, permitindo
# testar o projeto sem requerer chaves de API reais da OpenAI.
# =====================================================================

class MockChatOpenAI(BaseChatModel):
    model_name: str = "gpt-4o-mini"
    bound_tools: list = []

    def bind_tools(self, tools: list, **kwargs: Any) -> Runnable:
        """Registra as ferramentas associadas ao agente."""
        self.bound_tools = tools
        return self

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        # Encontra a última mensagem de texto enviada pelo usuário
        user_input = ""
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                user_input = msg.content.lower()
                break

        # Verifica se já temos respostas de ferramentas no histórico
        has_customer_info = False
        has_logistics_info = False
        has_logistics_error = False

        for msg in messages:
            if isinstance(msg, ToolMessage):
                if "Cliente:" in msg.content or "search_customer_db" in msg.name:
                    has_customer_info = True
                if "Pedido" in msg.content or "call_logistics_api" in msg.name:
                    has_logistics_info = True
                if "ValueError" in msg.content or "Error" in msg.content:
                    has_logistics_error = True

        ai_msg = None

        # --- CENÁRIO 3: LOOP REPETITIVO INDUZIDO ---
        if "loop" in user_input:
            # Força o agente a sempre tomar a decisão de chamar o banco de dados
            # Isso gera um loop infinito (assistente -> ferramenta -> assistente)
            print("[LLM Mock] Cenário de Loop ativado. Decidindo chamar a ferramenta repetidamente...")
            tool_calls = [
                ToolCall(
                    name="search_customer_db",
                    args={"customer_name": "Ana Silva"},
                    id="call_loop_search"
                )
            ]
            ai_msg = AIMessage(
                content="Identifiquei a necessidade de buscar informações do cliente no banco de dados repetidamente.",
                tool_calls=tool_calls
            )

        # --- CENÁRIO 2: FALHA CONTROLADA ---
        elif "9901" in user_input:
            if not has_logistics_info and not has_logistics_error:
                # LLM decide chamar a API de logística com ID inválido "9901" (sem o caractere '#')
                print("[LLM Mock] Cenário de Falha Controlada. Decidindo chamar API com formato inválido...")
                tool_calls = [
                    ToolCall(
                        name="call_logistics_api",
                        args={"order_id": "9901"}, # Formato incorreto de propósito
                        id="call_fail_logistics"
                    )
                ]
                ai_msg = AIMessage(
                    content="Vou rastrear o status de entrega do pedido 9901 na API de logística.",
                    tool_calls=tool_calls
                )
            else:
                # Retorno após a falha da ferramenta
                print("[LLM Mock] Retornando resposta final após erro controlado na ferramenta...")
                ai_msg = AIMessage(
                    content="Infelizmente, ocorreu um erro ao consultar o sistema de logística para o ID '9901'. O sistema exige que o ID comece com '#'. O erro foi registrado na nossa telemetria com sucesso!"
                )

        # --- CENÁRIO 1: EXECUÇÃO BEM-SUCEDIDA ---
        else:
            if not has_customer_info:
                # 1ª Ação: Buscar dados do cliente Ana Silva
                print("[LLM Mock] Cenário Sucesso. Ação 1: Consultando banco de dados de clientes...")
                tool_calls = [
                    ToolCall(
                        name="search_customer_db",
                        args={"customer_name": "Ana Silva"},
                        id="call_ok_search"
                    )
                ]
                ai_msg = AIMessage(
                    content="Entendido. Primeiramente vou consultar o banco de dados de clientes para verificar os dados da Ana Silva.",
                    tool_calls=tool_calls
                )
            elif has_customer_info and not has_logistics_info:
                # 2ª Ação: Rastrear o pedido correspondente (#9834) retornado da primeira ferramenta
                print("[LLM Mock] Cenário Sucesso. Ação 2: Consultando API de logística...")
                tool_calls = [
                    ToolCall(
                        name="call_logistics_api",
                        args={"order_id": "#9834"},
                        id="call_ok_logistics"
                    )
                ]
                ai_msg = AIMessage(
                    content="Banco de dados respondeu. Agora que sei que o último pedido da Ana é o #9834, vou consultar o status de rastreamento na API de logística.",
                    tool_calls=tool_calls
                )
            else:
                # 3ª Ação: Consolidação final com sucesso
                print("[LLM Mock] Cenário Sucesso. Finalizando atendimento com sucesso...")
                ai_msg = AIMessage(
                    content="Perfeito! Consegui consolidar as informações do seu atendimento:\n\n"
                            "1. **Cadastro do Cliente**: Ana Silva possui plano **Premium** e está com cadastro ativo.\n"
                            "2. **Logística**: O último pedido dela foi o **#9834** e consta como **Entregue** pela DirectLog em 28/05/2026.\n\n"
                            "Toda essa sequência de tomadas de decisão foi rastreada com sucesso!"
                )

        generation = ChatGeneration(message=ai_msg)
        return ChatResult(generations=[generation])

    @property
    def _llm_type(self) -> str:
        return "mock_chat_openai"


# =====================================================================
# 2. Definição das Ferramentas (Tools) em Python
# =====================================================================

@tool
def search_customer_db(customer_name: str) -> str:
    """Consulta o banco de dados de clientes para obter status do plano e ID do último pedido."""
    print(f"[Tool] search_customer_db executada para: '{customer_name}'")
    name_lower = customer_name.lower()
    if "ana" in name_lower:
        return "Cliente: Ana Silva | Plano: Premium | Status: Ativo | Último Pedido: #9834"
    elif "bruno" in name_lower:
        return "Cliente: Bruno Souza | Plano: Free | Status: Bloqueado | Último Pedido: #9521"
    else:
        return f"Cliente '{customer_name}' não localizado no banco de dados."


@tool
def call_logistics_api(order_id: str) -> str:
    """Consulta a API do sistema de logística para rastrear o status de um pedido pelo ID."""
    print(f"[Tool] call_logistics_api executada para: '{order_id}'")
    
    # CENÁRIO 2: Falha controlada induzida se o ID não iniciar com '#'
    if not order_id.startswith("#"):
        # Lançamos um erro explícito que será capturado como exceção estruturada nos spans do Phoenix
        raise ValueError(
            f"Erro na API de Logística: Formato de ID '{order_id}' é inválido. "
            f"O ID do pedido deve iniciar obrigatoriamente com o caractere '#' (Exemplo: #1234)."
        )
        
    if "9834" in order_id:
        return "Pedido #9834: Entregue em 28/05/2026 pela transportadora DirectLog."
    elif "9521" in order_id:
        return "Pedido #9521: Aguardando aprovação de pagamento."
    else:
        return f"Pedido '{order_id}' não localizado no sistema de logística."


# Lista consolidada de ferramentas
tools = [search_customer_db, call_logistics_api]
tool_node = ToolNode(tools)


# =====================================================================
# 3. Definição do Estado e do Grafo do Agente (LangGraph)
# =====================================================================

class AgentState(TypedDict):
    # O estado armazena a sequência acumulada de mensagens
    messages: Annotated[Sequence[BaseMessage], operator.add]


# Definição do Nó do Assistente (chama o LLM Mock com ferramentas vinculadas)
def call_model(state: AgentState) -> Dict[str, Any]:
    print("[Grafo] Nó do Assistente: chamando LLM...")
    model = MockChatOpenAI()
    model = model.bind_tools(tools)
    response = model.invoke(state["messages"])
    return {"messages": [response]}


# Definição da lógica de decisão de fluxo (Roteador Condicional)
def should_continue(state: AgentState) -> str:
    last_message = state["messages"][-1]
    # Se o LLM emitiu chamadas de ferramentas, segue para o nó de ferramentas
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        print(f"[Grafo] Roteador: LLM solicitou ferramentas -> {last_message.tool_calls[0].name}")
        return "tools"
    # Caso contrário, encerra o fluxo do grafo
    print("[Grafo] Roteador: Fim da execução")
    return END


# Montagem física do Grafo
workflow = StateGraph(AgentState)

# Adiciona os nós
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)

# Define o ponto de entrada
workflow.set_entry_point("agent")

# Define as arestas
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        END: END
    }
)

# Aresta de retorno das ferramentas para o agente
workflow.add_edge("tools", "agent")

# Compila o grafo
graph = workflow.compile()
