// frontend/src/types/chat.ts

// Tipos permitidos para os papéis (roles) nas mensagens
export type Role = 'user' | 'assistant' | 'system' | 'tool';

export interface ChatMessage {
  id?: string; // Opcional, pois mensagens novas enviadas pelo usuário ainda não tem ID
  role: Role;
  content: string;
  created_at?: string;
}

// Representa a versão resumida da conversa (usada na Sidebar)
export interface ConversationSummary {
  id: string;
  title: string;
  created_at: string;
  updated_at?: string | null;
}

// Representa o detalhe da conversa (usada na área principal do chat)
export interface ConversationHistory {
  id: string;
  title: string;
  created_at: string;
  messages: ChatMessage[];
}

export interface ChatRequest {
  message: string;
  conversation_id?: string | null; // Se for null, o backend entende que é uma nova conversa
}

// Alinhado exatamente com o schema ToolCallInfo do seu Backend (app/schemas/agent.py)
export interface ToolCallInfo {
  tool_name: string;
  arguments: Record<string, any>;
  success: boolean;
}

// Alinhado exatamente com o schema ChatResponse do seu Backend (app/schemas/agent.py)
export interface ChatResponse {
  conversation_id: string;
  response: string;
  tools_used: ToolCallInfo[];
}