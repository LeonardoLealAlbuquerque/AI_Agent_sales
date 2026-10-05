// frontend/src/services/api.ts
import type { 
  ConversationSummary, 
  ConversationHistory, 
  ChatRequest, 
  ChatResponse 
} from '../types/chat';

type MessageChunkHandler = (chunk: string) => void;

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const api = {
  getConversations: async (): Promise<ConversationSummary[]> => {
    const response = await fetch(`${API_BASE_URL}/api/v1/agent/conversations`);
    if (!response.ok) {
      throw new Error('Falha ao buscar lista de conversas');
    }
    const data = await response.json();
    return data.map((conversation: ConversationSummary & { conversation_id?: string }) => ({
      ...conversation,
      id: conversation.id || conversation.conversation_id || '',
    }));
  },

  getConversationHistory: async (conversationId: string): Promise<ConversationHistory> => {
    const response = await fetch(`${API_BASE_URL}/api/v1/agent/conversations/${conversationId}`);
    if (!response.ok) {
      throw new Error('Falha ao buscar histórico da conversa');
    }
    return response.json();
  },

  deleteConversation: async (conversationId: string): Promise<void> => {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/agent/conversations/${encodeURIComponent(conversationId)}`,
      { method: 'DELETE' },
    );
    if (!response.ok) {
      throw new Error('Falha ao excluir conversa');
    }
  },

  sendMessage: async (data: ChatRequest, onChunk?: MessageChunkHandler): Promise<ChatResponse> => {
    const response = await fetch(`${API_BASE_URL}/api/v1/agent/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      throw new Error('Falha ao enviar mensagem para o agente');
    }

    if (!response.body) {
      return response.json();
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    const separator = '\n|||\n';
    let pending = '';
    let metadata: Partial<ChatResponse> | null = null;
    let completeResponse = '';

    const emitText = (text: string) => {
      if (!text) return;
      completeResponse += text;
      onChunk?.(text);
    };

    while (true) {
      const { value, done } = await reader.read();
      pending += decoder.decode(value, { stream: !done });

      if (metadata === null) {
        const separatorIndex = pending.indexOf(separator);
        if (separatorIndex >= 0) {
          const metadataText = pending.slice(0, separatorIndex);
          metadata = JSON.parse(metadataText) as Partial<ChatResponse>;
          pending = pending.slice(separatorIndex + separator.length);
          emitText(pending);
          pending = '';
        }
      } else {
        emitText(pending);
        pending = '';
      }

      if (done) break;
    }

    if (metadata === null) {
      throw new Error('Resposta do agente em formato inválido');
    }

    return {
      conversation_id: metadata.conversation_id || '',
      response: completeResponse,
      tools_used: metadata.tools_used || [],
    };
  }
};