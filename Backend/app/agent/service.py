# app/agent/service.py (Trecho com Observabilidade)

import json
import logging
from typing import List, Dict, Any
from app.agent.llm_client import BaseLLMClient, RealLLMClient
from app.agent.prompts import B2B_SALES_AGENT_SYSTEM_PROMPT
from app.agent.tools import GROQ_TOOL_SCHEMAS, execute_tool
from app.schemas.agent import ChatRequest, ChatResponse, ToolCallInfo

logger = logging.getLogger("b2b_agent.orchestrator")


class AgentService:
    def __init__(self, llm_client: BaseLLMClient = None):
        self.llm_client = llm_client or RealLLMClient()

    def run(self, request: ChatRequest) -> ChatResponse:
        logger.info(f"[AGENT START] Sessão: {request.conversation_id} | Mensagem: '{request.message}'")
        
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": B2B_SALES_AGENT_SYSTEM_PROMPT}
        ]
        for msg in request.history:
            messages.append({"role": msg.role, "content": msg.content})

        messages.append({"role": "user", "content": request.message})
        tools_used: List[ToolCallInfo] = []
        max_turns = 5

        for turn in range(max_turns):
            logger.debug(f"[AGENT TURN {turn + 1}/{max_turns}] Enviando contexto ao Groq/Qwen...")
            
            response = self.llm_client.chat_completion(
                messages=messages,
                tools=GROQ_TOOL_SCHEMAS
            )

            choice = response.choices[0]
            message = choice.message

            if hasattr(message, "tool_calls") and message.tool_calls:
                messages.append({
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": message.tool_calls
                })

                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                    except Exception as e:
                        logger.error(f"[TOOL ARG ERROR] Falha ao parsear argumentos da tool {tool_name}: {str(e)}")
                        arguments = {}

                    logger.info(f"[TOOL EXECUTION] Chamando {tool_name} com args: {arguments}")
                    tool_result = execute_tool(tool_name, arguments)
                    
                    is_success = "error" not in tool_result
                    tools_used.append(ToolCallInfo(
                        tool_name=tool_name,
                        arguments=arguments,
                        success=is_success
                    ))

                    if not is_success:
                        logger.warning(f"[TOOL FAIL] {tool_name} retornou erro: {tool_result}")

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result
                    })
            else:
                logger.info(f"[AGENT END] Resposta final gerada com sucesso. Tools utilizadas: {len(tools_used)}")
                return ChatResponse(
                    conversation_id=request.conversation_id,
                    response=message.content or "Não foi possível obter uma resposta conclusiva.",
                    tools_used=tools_used
                )

        logger.warning(f"[AGENT TIMEOUT] Limite de {max_turns} iterações atingido na sessão {request.conversation_id}")
        return ChatResponse(
            conversation_id=request.conversation_id,
            response=message.content or "Limite máximo de iterações de ferramentas atingido.",
            tools_used=tools_used
        )