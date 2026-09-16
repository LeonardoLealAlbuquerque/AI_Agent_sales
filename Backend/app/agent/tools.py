# app/agent/tools.py

import json
from typing import Dict, Any, Callable

# Importação das funções oficiais de app/api/tools.py (Única Fonte de Verdade)
from app.api.tools import (
    get_client_risk_analysis,
    get_client_credit_limit,
    get_overdue_invoices,
    get_client_orders,
    get_order_details
)

# --- Mapeamento de Execução para Dispatcher ---
AVAILABLE_TOOLS_MAP: Dict[str, Callable[..., Any]] = {
    "get_client_risk_analysis": get_client_risk_analysis,
    "get_client_credit_limit": get_client_credit_limit,
    "get_overdue_invoices": get_overdue_invoices,
    "get_client_orders": get_client_orders,
    "get_order_details": get_order_details,
}

# --- Schemas de Function Calling para o Groq / OpenAI ---
GROQ_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_client_risk_analysis",
            "description": "Analisa o risco de crédito e financeiro consolidado de um cliente com base em seu ID no sistema.",
            "parameters": {
                "type": "object",
                "properties": {
                    "client_id": {
                        "type": "integer",
                        "description": "ID único do cliente."
                    }
                },
                "required": ["client_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_client_credit_limit",
            "description": "Consulta o limite de crédito total, utilizado e disponível de um cliente específico.",
            "parameters": {
                "type": "object",
                "properties": {
                    "client_id": {
                        "type": "integer",
                        "description": "ID único do cliente."
                    }
                },
                "required": ["client_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_overdue_invoices",
            "description": "Lista todas as faturas vencidas e em aberto associadas a um cliente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "client_id": {
                        "type": "integer",
                        "description": "ID único do cliente."
                    }
                },
                "required": ["client_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_client_orders",
            "description": "Recupera o histórico completo de pedidos de venda de um cliente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "client_id": {
                        "type": "integer",
                        "description": "ID único do cliente."
                    }
                },
                "required": ["client_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_order_details",
            "description": "Obtém os detalhes e itens de um pedido específico com base no ID do pedido.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "integer",
                        "description": "ID único do pedido de venda."
                    }
                },
                "required": ["order_id"]
            }
        }
    }
]


def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    """
    Despacha a execução para a ferramenta subjacente de `app/api/tools.py`
    e serializa o resultado em JSON seguro para envio de volta ao LLM.
    """
    if tool_name not in AVAILABLE_TOOLS_MAP:
        return json.dumps({"error": f"Ferramenta desconhecida: {tool_name}"}, ensure_ascii=False)
    
    tool_func = AVAILABLE_TOOLS_MAP[tool_name]
    try:
        # Executa a função oficial importada
        result = tool_func(**arguments)

        if isinstance(result, str):
            return result
        if hasattr(result, "model_dump"):
            data = result.model_dump(mode="json")
        elif hasattr(result, "dict"):
            data = result.dict()
        else:
            data = result

        return json.dumps(data, ensure_ascii=False)
    
    except Exception as e:
        return json.dumps({"error": f"Erro na execução da ferramenta {tool_name}: {str(e)}"}, ensure_ascii=False)