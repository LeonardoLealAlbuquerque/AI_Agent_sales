from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from groq import Groq, APITimeoutError, APIConnectionError, APIStatusError
from app.core.config import settings

# --- Exceções Customizadas do LLM ---
class LLMError(Exception):
    """Erro base para falhas relacionadas ao LLM."""
    pass

class LLMTimeoutError(LLMError):
    """Exceção acionada quando o LLM excede o tempo limite de resposta."""
    pass

class LLMUnavailableError(LLMError):
    """Exceção acionada quando o provedor de LLM está inacessível."""
    pass


# --- Contrato (Abstração) ---
class BaseLLMClient(ABC):
    @abstractmethod
    def chat_completion(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Any:
        """Executa uma chamada de chat completion no modelo."""
        pass


# --- Implementação Real (Groq SDK Oficial) ---
class RealLLMClient(BaseLLMClient):
    def __init__(self):
        # Inicializa o cliente oficial do Groq
        self.client = Groq(
            api_key=settings.LLM_API_KEY,
            timeout=settings.LLM_TIMEOUT
        )
        self.model = settings.LLM_MODEL

    def chat_completion(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None, stream_response: bool = False) -> Any:
        try:
            kwargs: Dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "max_tokens": settings.LLM_MAX_TOKENS,
                "stream": stream_response
            }
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"
                kwargs["parallel_tool_calls"] = True
                kwargs["stream"] = False  

            response = self.client.chat.completions.create(**kwargs)
            return response

        except APITimeoutError as e:
            raise LLMTimeoutError("❌ O Groq excedeu o tempo limite (timeout) na resposta.") from e
        except APIConnectionError as e:
            raise LLMUnavailableError("❌ Não foi possível estabelecer conexão com a API do Groq.") from e
        except APIStatusError as e:
            raise LLMError(f"❌ Erro HTTP retornado pela API do Groq [Status {e.status_code}]: {e.message}") from e
        except Exception as e:
            raise LLMError(f"❌ Erro inesperado na comunicação com o Groq: {str(e)}") from e


# --- Double de Teste (Mock para Testes Unitários/Integração) ---
class MockLLMClient(BaseLLMClient):
    """
    Cliente simulado para testes utilizando Groq. Permite injetar respostas pré-programadas,
    simular timeouts ou falhas de conexão sem disparar chamadas de rede.
    """
    def __init__(
        self, 
        canned_response: Any = None, 
        should_timeout: bool = False, 
        should_fail: bool = False
    ):
        self.canned_response = canned_response
        self.should_timeout = should_timeout
        self.should_fail = should_fail
        self.last_messages: List[Dict[str, Any]] = []
        self.last_tools: Optional[List[Dict[str, Any]]] = None

    def chat_completion(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Any:
        self.last_messages = messages
        self.last_tools = tools

        if self.should_timeout:
            raise LLMTimeoutError("Simulação de Timeout no cliente Groq.")
        if self.should_fail:
            raise LLMUnavailableError("Simulação de Indisponibilidade no cliente Groq.")

        if self.canned_response:
            return self.canned_response

        class MockMessage:
            def __init__(self, content: Optional[str], tool_calls: Optional[List[Any]] = None):
                self.content = content
                self.tool_calls = tool_calls

        class MockChoice:
            def __init__(self, message: MockMessage):
                self.message = message

        class MockResponse:
            def __init__(self, choice: MockChoice):
                self.choices = [choice]

        return MockResponse(MockChoice(MockMessage(content="Resposta simulada do Agente B2B via Groq com sucesso.")))