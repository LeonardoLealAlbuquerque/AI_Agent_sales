import json
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Iterator
from sqlalchemy.orm import Session

from app.agent.llm_client import BaseLLMClient, RealLLMClient
from app.agent.prompts import B2B_SALES_AGENT_SYSTEM_PROMPT
from app.agent.tools import GROQ_TOOL_SCHEMAS, execute_tool
from app.schemas.agent import ChatRequest, ToolCallInfo
from app.repositories.conversation_repository import ConversationRepository
from app.db.session import SessionLocal  # Import adicionado

logger = logging.getLogger("b2b_agent.orchestrator")


class AgentService:
    def __init__(self, llm_client: BaseLLMClient = None, db: Session | None = None):
        self.llm_client = llm_client or RealLLMClient()
        self.db = db

    def run(self, request: ChatRequest) -> Iterator[str]:
        logger.info(f"[AGENT START] Sessão: {request.conversation_id} | Mensagem: '{request.message}'")
        
        conversation = None
        repository = ConversationRepository(self.db) if self.db else None
        if repository:
            if request.conversation_id:
                conversation = repository.get(request.conversation_id)
                if conversation is None:
                    raise ValueError("Conversa não encontrada.")
            else:
                conversation = repository.create(request.message[:200])
            stored_history = repository.get_messages_for_llm(conversation.id)
        else:
            stored_history = []

        conversation_id = conversation.id if conversation else None
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": B2B_SALES_AGENT_SYSTEM_PROMPT}
        ]

        history = (stored_history or request.history)[-10:]
        messages.extend(history)

        messages.append({"role": "user", "content": request.message})
        if repository and conversation_id:
            repository.add_message(conversation_id, role="user", content=request.message)
            self.db.commit()

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
                serialized_tool_calls = [
                    tc if isinstance(tc, dict) else tc.model_dump()
                    for tc in message.tool_calls
                ]
                messages.append({
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": serialized_tool_calls
                })

                if repository and conversation_id:
                    repository.add_message(
                        conversation_id=conversation_id,
                        role="assistant",
                        content=message.content,
                        tool_calls=serialized_tool_calls
                    )
                    self.db.commit()

                def run_tool(tool_call: Any) -> tuple[Any, Dict[str, Any], str]:
                    if isinstance(tool_call, dict):
                        function = tool_call.get("function", {})
                        tool_name = function.get("name", "")
                        raw_arguments = function.get("arguments", "{}")
                    else:
                        function = tool_call.function
                        tool_name = function.name
                        raw_arguments = function.arguments
                    try:
                        arguments = json.loads(raw_arguments) if isinstance(raw_arguments, str) else raw_arguments
                    except Exception:
                        arguments = {}
                    logger.info(f"[TOOL EXECUTION] Chamando {tool_name} com args: {arguments}")

                    return tool_call, arguments, execute_tool(tool_name, arguments)

                with ThreadPoolExecutor(max_workers=len(message.tool_calls)) as executor:
                    tool_results = list(executor.map(run_tool, message.tool_calls))

                for tool_call, arguments, tool_result in tool_results:
                    if isinstance(tool_call, dict):
                        tool_name = tool_call.get("function", {}).get("name", "")
                        tool_call_id = tool_call.get("id", "")
                    else:
                        tool_name = tool_call.function.name
                        tool_call_id = tool_call.id
                    
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
                        "tool_call_id": tool_call_id,
                        "name": tool_name,
                        "content": tool_result
                    })

                    if repository and conversation_id:
                        repository.add_message(
                            conversation_id=conversation_id,
                            role="tool",
                            content=tool_result,
                            tool_call_id=tool_call_id,
                            name=tool_name
                        )
                if repository and conversation_id:
                    self.db.commit()
            else:
                logger.info(f"[AGENT END] Resposta final gerada com sucesso. Tools utilizadas: {len(tools_used)}")
                
                def gerador_de_streaming():
                    tools_data = [t.dict() if hasattr(t, 'dict') else t.__dict__ for t in tools_used]
                    dados_ferramentas = json.dumps({"tools_used": tools_data}, ensure_ascii=False)
                    yield f"{dados_ferramentas}\n|||\n"

                    texto_completo = ""
                    try:
                        stream_resp = self.llm_client.chat_completion(
                            messages=messages,
                            tools=None,           
                            stream_response=True  
                        )

                        for chunk in stream_resp:
                            if hasattr(chunk.choices[0], 'delta') and chunk.choices[0].delta.content:
                                pedaco = chunk.choices[0].delta.content
                                texto_completo += pedaco
                                yield pedaco
                    except Exception as e:
                        logger.error(f"[STREAM ERROR] Falha na conexão de streaming: {e}")
                        if "Tool choice is none" in str(e) or "model called a tool" in str(e):
                            fallback = "\n\nSua solicitação retornou múltiplos resultados ou os dados fornecidos não foram suficientes para localizar a informação exata. Por medida de segurança corporativa, a busca foi pausada. Por favor, seja mais específico (informe um ID exato, CNPJ, número da fatura ou pedido)."
                            texto_completo += fallback  
                            yield fallback            
                        else:
                            erro_generico = "\n\n[Ocorreu um erro ao transmitir a resposta completa.]"
                            texto_completo += erro_generico
                            yield erro_generico
                    finally: 
                        if conversation_id and texto_completo.strip():
                            db_stream = SessionLocal()
                            try: 
                                repo_stream = ConversationRepository(db_stream)
                                repo_stream.add_message(
                                    conversation_id=conversation_id,
                                    role="assistant",
                                    content=texto_completo,
                                )
                                db_stream.commit()
                            except Exception as db_err:
                                logger.error(f"[DB ERROR] Erro ao salvar mensagem final: {db_err}")
                                db_stream.rollback()
                            finally:
                                db_stream.close()
                                
                return gerador_de_streaming()

        logger.warning(f"[AGENT TIMEOUT] Limite de {max_turns} iterações atingido na sessão {request.conversation_id}")
        def gerador_de_timeout():
            dados_ferramentas = json.dumps(
                {"tools_used": [t.dict() if hasattr(t, 'dict') else t.__dict__ for t in tools_used]}, 
                ensure_ascii=False
            )
            yield f"{dados_ferramentas}\n|||\n"
            msg_timeout = "Limite máximo de processamento atingido. Por favor, seja mais específico na sua pergunta."
            yield msg_timeout
            
            if repository and conversation_id:
                repository.add_message(conversation_id, role="assistant", content=f"Erro: {msg_timeout}")
                self.db.commit()

        return gerador_de_timeout()