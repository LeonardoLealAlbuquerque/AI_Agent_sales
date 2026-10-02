import { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { ChatArea } from './components/ChatArea';
import { ChatInput } from './components/ChatInput';
import { api } from './services/api';
import type { ConversationSummary, ChatMessage } from './types/chat';

export default function App() {
  const navigate = useNavigate();
  const { conversationId } = useParams<{ conversationId: string }>();
  const currentConversationId = conversationId ?? null;
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  const [isLoadingSidebar, setIsLoadingSidebar] = useState(false);
  const [sidebarError, setSidebarError] = useState<string | null>(null);
  const [isLoadingChat, setIsLoadingChat] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);

  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const [isDesktopSidebarOpen, setIsDesktopSidebarOpen] = useState(true);
  const [conversationReloadKey, setConversationReloadKey] = useState(0);
  const preserveMessagesForConversation = useRef<string | null>(null);

  const fetchConversations = async (silent = false) => {
    try {
      setSidebarError(null);
      if (!silent) setIsLoadingSidebar(true);

      const data = await api.getConversations();
      const sorted = data.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
      setConversations(sorted);
    } catch (error) {
      console.error('Erro:', error);
      setSidebarError("Não foi possível carregar o histórico.");
    } finally {
      if (!silent) setIsLoadingSidebar(false);
    }
  };

  useEffect(() => {
    fetchConversations();
  }, []);

  useEffect(() => {
    if (!currentConversationId) {
      setMessages([]);
      setChatError(null);
      setIsLoadingChat(false);
      return;
    }

    if (preserveMessagesForConversation.current === currentConversationId) {
      preserveMessagesForConversation.current = null;
      setIsLoadingChat(false);
      return;
    }

    let isCurrentConversation = true;
    setMessages([]);
    setChatError(null);
    setIsLoadingChat(true);

    api.getConversationHistory(currentConversationId)
      .then(history => {
        if (isCurrentConversation) setMessages(history.messages);
      })
      .catch(error => {
        console.error('Erro:', error);
        if (isCurrentConversation) setChatError('Não foi possível carregar as mensagens.');
      })
      .finally(() => {
        if (isCurrentConversation) setIsLoadingChat(false);
      });

    return () => {
      isCurrentConversation = false;
    };
  }, [currentConversationId, conversationReloadKey]);

  const handleSelectConversation = (id: string) => {
    if (id === currentConversationId) {
      setIsMobileSidebarOpen(false); 
      return;
    }

    setIsMobileSidebarOpen(false);
  setMessages([]);
    navigate(`/${encodeURIComponent(id)}`);
  };

  const handleNewConversation = () => {
    navigate('/');
    setMessages([]);
    setChatError(null);
    setIsMobileSidebarOpen(false);
  };

  const handleSendMessage = async (text: string) => {
    if (!text.trim() || isLoadingChat) return;

    setChatError(null);
    const assistantMessageId = `assistant-${Date.now()}`;
    setMessages(prev => [
      ...prev,
      { role: 'user', content: text },
      { id: assistantMessageId, role: 'assistant', content: '' },
    ]);
    setIsLoadingChat(true);

    try {
      const response = await api.sendMessage(
        { message: text, conversation_id: currentConversationId },
        (chunk) => {
          setMessages(prev => prev.map(message => (
            message.id === assistantMessageId
              ? { ...message, content: message.content + chunk }
              : message
          )));
        },
      );

      setMessages(prev => prev.map(message => (
        message.id === assistantMessageId && !message.content.trim()
          ? { ...message, content: response.response?.trim() || "Desculpe, não consegui formular uma resposta no momento." }
          : message
      )));

      if (!currentConversationId) {
        preserveMessagesForConversation.current = response.conversation_id;
        navigate(`/${encodeURIComponent(response.conversation_id)}`, { replace: true });
      }
      fetchConversations(true);
    } catch (error) {
      console.error('Erro:', error);
      setMessages(prev => [
        ...prev.filter(message => message.id !== assistantMessageId),
        { role: 'system', content: 'Erro de conexão. Tente novamente.' },
      ]);
    } finally {
      setIsLoadingChat(false);
    }
  };

  const currentTitle = conversations.find(c => c.id === currentConversationId)?.title || 'Nova Conversa';

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50 font-sans w-full">

      {/* NOVO: Overlay do Mobile quando menu está aberto */}
      {isMobileSidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden transition-opacity"
          onClick={() => setIsMobileSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      <Sidebar
        conversations={conversations}
        currentConversationId={currentConversationId}
        isLoading={isLoadingSidebar}
        error={sidebarError}
        isOpen={isMobileSidebarOpen}
        isDesktopOpen={isDesktopSidebarOpen}
        onToggleDesktop={() => setIsDesktopSidebarOpen((isOpen) => !isOpen)}
        onClose={() => setIsMobileSidebarOpen(false)}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
        onRetry={() => fetchConversations()}
      />

      <div className="flex-1 flex flex-col relative h-full w-full">
        <header className="bg-zinc-800 border-b border-gray-200 px-4 md:px-6 py-4 flex items-center justify-between shadow-sm z-10">
          <div className="flex items-center flex-1 overflow-hidden">
            <button
              onClick={() => setIsMobileSidebarOpen(true)}
              className="mr-3 p-2 -ml-2 text-gray-600 hover:bg-gray-100 rounded-lg md:hidden focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label="Abrir menu de conversas"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <div className="flex items-center min-w-0 w-180">
              <h2 className="text-lg font-semibold text-gray-800 truncate pr-4" title={currentTitle}>
                {currentTitle}
              </h2>
            </div>
          </div>
          <span className={`text-xs px-2 py-1 rounded-full font-medium whitespace-nowrap ${sidebarError || chatError ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
            }`}>
            {sidebarError || chatError ? 'Offline' : 'Online'}
          </span>
        </header>

        <ChatArea
          messages={messages}
          isLoading={isLoadingChat}
          error={chatError}
          onRetry={() => currentConversationId ? setConversationReloadKey(key => key + 1) : null}
        />

        <ChatInput
          onSendMessage={handleSendMessage}
          isLoading={isLoadingChat}
        />
      </div>
    </div>
  );
}