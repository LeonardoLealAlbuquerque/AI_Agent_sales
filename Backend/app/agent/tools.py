import json
from typing import Dict, Any, Callable
from langchain_core.tools import tool

from app.services.chromadb_service import ChromaDBService
from app.api.tools import (
    get_client_risk_analysis,
    get_client_credit_limit,
    list_clients,
    list_invoices,  
    get_client_orders,
    get_order_details
)

chroma_service = ChromaDBService()

@tool
def buscar_regras_negociacao(query: str) -> str:
    """
    Consulta a base de conhecimento oficial (Playbook B2B) sobre políticas de desconto,
    parcelamento, prazos e alçadas de decisão.
    
    A consulta 'query' é obrigatória.
    """
    if not query or not query.strip():
        return json.dumps({"error": "Parâmetro 'query' é obrigatório para buscar na KB."})

    try:
        results = chroma_service.search_similarity(query=query, n_results=3)
        
        if not results:
            return json.dumps({
                "status": "warning",
                "message": "Nenhuma regra específica encontrada na KB para esta consulta."
            }, ensure_ascii=False)

        formatted_chunks = []
        for idx, res in enumerate(results, 1):
            secao = res["metadata"].get("section", "Geral")
            distancia = res.get("distance", "N/A")
            content = res["content"]
            formatted_chunks.append(
                f"[Trecho {idx} - Seção: {secao} | Distância: {distancia}]\n{content}"
            )

        return json.dumps({
            "status": "success",
            "regras_encontradas": "\n\n".join(formatted_chunks)
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "error": f"Base de Conhecimento (KB) temporariamente indisponível: {str(e)}"
        }, ensure_ascii=False)


AVAILABLE_TOOLS_MAP: Dict[str, Callable[..., Any]] = {
    "get_client_risk_analysis": get_client_risk_analysis,
    "get_client_credit_limit": get_client_credit_limit,
    "list_clients": list_clients,
    "list_invoices": list_invoices,  
    "get_client_orders": get_client_orders,
    "get_order_details": get_order_details,
    "buscar_regras_negociacao": buscar_regras_negociacao.func,
}

GROQ_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "list_clients",
            "description": "Busca cadastros de clientes com filtros combináveis por ID, nome parcial, CNPJ, limite de crédito e status. Use os IDs retornados para consultar risco ou crédito.",
            "parameters": {
                "type": "object",
                "properties": {
                    "client_id": {"type": "integer", "description": "ID exato do cliente."},
                    "name": {"type": "string", "description": "Parte do nome da empresa."},
                    "cnpj": {"type": "string", "description": "CNPJ completo ou trecho; aceita máscara."},
                    "credit_limit": {"type": "number", "description": "Limite de crédito exato."},
                    "min_credit_limit": {"type": "number", "description": "Limite mínimo, inclusive."},
                    "max_credit_limit": {"type": "number", "description": "Limite máximo, inclusive."},
                    "status": {"type": "string", "description": "Status exato do cadastro, por exemplo ACTIVE ou INACTIVE."},
                    "limit": {"type": "integer", "description": "Quantidade máxima de clientes (padrão 50, máximo 100)."},
                    "skip": {"type": "integer", "description": "Quantidade de resultados ignorados para paginação."}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_client_risk_analysis",
            "description": "Analisa o risco financeiro consolidado. Use client_id ou o nome completo/parcial do cliente quando o ID não for informado.",
            "parameters": {
                "type": "object",
                "properties": {
                    "client_id": {"type": "integer", "description": "ID único do cliente."},
                    "name": {"type": "string", "description": "Nome completo ou parcial do cliente."}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_client_credit_limit",
            "description": "Consulta o limite de crédito. Use client_id ou o nome completo/parcial do cliente quando o ID não for informado.",
            "parameters": {
                "type": "object",
                "properties": {
                    "client_id": {"type": "integer", "description": "ID único do cliente."},
                    "name": {"type": "string", "description": "Nome completo ou parcial do cliente."}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_invoices",
            "description": "Consulta faturas. Para localizar uma empresa por nome parcial, CNPJ ou ID da fatura, use o parâmetro search; client_id não é obrigatório. Permite combinar a busca com status, atraso, faixa de valores e intervalo de datas de pagamento.",
            "parameters": {
                "type": "object",
                "properties": {
                    "search": {
                        "type": "string",
                        "description": "Busca por nome da empresa, CNPJ ou ID numérico da fatura."
                    },
                    "client_id": {
                        "type": "integer",
                        "description": "ID do cliente para filtrar faturas de uma empresa específica."
                    },
                    "status": {
                        "type": "string",
                        "enum": ["PENDING", "PAID", "CANCELED"],
                        "description": "Filtra pelo status exato da fatura."
                    },
                    "only_overdue": {
                        "type": "boolean",
                        "description": "Defina como true para listar APENAS faturas pendentes que estão atrasadas/vencidas."
                    },
                    "min_amount": {
                        "type": "number",
                        "description": "Valor mínimo da fatura, inclusive."
                    },
                    "max_amount": {
                        "type": "number",
                        "description": "Valor máximo da fatura, inclusive."
                    },
                    "payment_date_start": {
                        "type": "string",
                        "format": "date",
                        "description": "Data mínima de pagamento, no formato YYYY-MM-DD."
                    },
                    "payment_date_end": {
                        "type": "string",
                        "format": "date",
                        "description": "Data máxima de pagamento, no formato YYYY-MM-DD."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Quantidade máxima de faturas a retornar (padrão 50)."
                    },
                    "skip": {
                        "type": "integer",
                        "description": "Quantidade de faturas a ignorar para paginação."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_client_orders",
            "description": "Recupera o histórico de pedidos. Use client_id ou o nome completo/parcial do cliente quando o ID não for informado.",
            "parameters": {
                "type": "object",
                "properties": {
                    "client_id": {"type": "integer", "description": "ID único do cliente."},
                    "name": {"type": "string", "description": "Nome completo ou parcial do cliente."}
                },
                "required": []
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
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_regras_negociacao",
            "description": "Consulta a base de conhecimento oficial (Playbook B2B) sobre políticas de desconto, parcelamento, prazos e alçadas de decisão.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A dúvida ou termo de busca relacionado com as regras de negócio B2B."
                    }
                },
                "required": ["query"]
            }
        }
    }
]


def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    """
    Despacha a execução para a ferramenta registrada e serializa o resultado em JSON.
    """
    if tool_name not in AVAILABLE_TOOLS_MAP:
        return json.dumps({"error": f"Ferramenta desconhecida: {tool_name}"}, ensure_ascii=False)
    
    tool_func = AVAILABLE_TOOLS_MAP[tool_name]
    try:
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