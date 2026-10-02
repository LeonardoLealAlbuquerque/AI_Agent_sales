import { useEffect, useRef } from 'react';
import { ChatMessage } from './ChatMessage';

export interface Message {
  id?: string;
  role: 'user' | 'assistant' | 'system' | 'tool'; 
  content: string;
}

// 1. ATUALIZADO: Adicionadas as props error e onRetry que vêm do App.tsx
interface ChatAreaProps {
  messages: Message[];
  isLoading?: boolean;
  error?: string | null; 
  onRetry?: () => void;  
}

export function ChatArea({ messages, isLoading, error, onRetry }: ChatAreaProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView?.({ behavior: 'smooth' });
  }, [messages, isLoading, error]); // Adicionado error na dependência do scroll

  const lastMessage = messages[messages.length - 1];

  return (
    <div className="flex-1 overflow-y-auto p-4 pb-20 bg-zinc-900">
      
      {/* 1. ESTADO VAZIO */}
      {messages.length === 0 && !error && (
        <div className="flex flex-col items-center justify-center h-full text-zinc-400">
          <h2 className="text-2xl font-semibold mb-2 text-zinc-200">
            Como posso ajudar hoje?
          </h2>
          <p className="text-sm text-zinc-500 text-center max-w-md">
            Pergunte sobre clientes, faturas em aberto ou análise de crédito.
          </p>
        </div>
      )}

      {/* 2. LISTA DE MENSAGENS */}
      {messages.map((message, index) => (
        <ChatMessage
          key={message.id || index}
          role={message.role}
          content={message.content}
        />
      ))}

      {/* 3. INDICADOR DE CARREGAMENTO */}
      {isLoading && (!lastMessage || lastMessage.role !== 'assistant' || !lastMessage.content) && (
        <div className="flex justify-start">
          <div className="bg-zinc-800 text-zinc-400 px-4 py-3 rounded-lg text-sm animate-pulse border border-zinc-700">
            Analisando dados e gerando resposta...
          </div>
        </div>
      )}

      {/* 4. NOVO: MENSAGEM DE ERRO COM BOTÃO DE RETRY NO CHAT */}
      {error && (
        <div className="flex flex-col items-center justify-center p-4 mt-4 bg-red-900/20 border border-red-800/50 rounded-lg">
          <p className="text-red-400 text-sm mb-3">{error}</p>
          {onRetry && (
            <button 
              onClick={onRetry}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded text-sm transition-colors"
            >
              Tentar novamente
            </button>
          )}
        </div>
      )}

      {/* Âncora invisível ganha um respiro extra na rolagem */}
      <div ref={messagesEndRef} className="h-4" />
    </div>
  );
}