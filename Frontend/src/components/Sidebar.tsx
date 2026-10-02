import type { ConversationSummary } from '../types/chat';

interface SidebarProps {
  conversations: ConversationSummary[];
  currentConversationId: string | null;
  isLoading: boolean;
  error: string | null;
  isOpen: boolean; // Novo: controla exibição mobile
  isDesktopOpen: boolean;
  onToggleDesktop: () => void;
  onClose: () => void; // Novo: fechar no mobile
  onSelectConversation: (id: string) => void;
  onNewConversation: () => void;
  onRetry: () => void;
}

export function Sidebar({ 
  conversations, currentConversationId, isLoading, error,
  isOpen, isDesktopOpen, onToggleDesktop, onClose, onSelectConversation, onNewConversation, onRetry
}: SidebarProps) {
  const formatDate = (dateString: string) => {
    if (!dateString) return '';
    return new Date(dateString).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' });
  };

  return (
    <aside 
      className={`fixed inset-y-0 left-0 z-50 w-64 bg-gray-900 text-white flex flex-col h-screen transform transition-[transform,width] duration-300 ease-in-out md:relative md:translate-x-0 md:flex-shrink-0 md:overflow-hidden ${
        isOpen ? 'translate-x-0' : '-translate-x-full'
      } ${
        isDesktopOpen ? 'md:w-64' : 'md:w-14'
      }`}
      aria-label="Menu Lateral"
    >
      <div className={`p-2 md:p-4 flex gap-2 items-center ${isDesktopOpen ? '' : 'md:justify-center'}`}>
        <button
          onClick={onToggleDesktop}
          aria-label={isDesktopOpen ? 'Recolher menu de conversas' : 'Expandir menu de conversas'}
          aria-expanded={isDesktopOpen}
          aria-controls="conversation-history"
          className="hidden md:flex shrink-0 items-center justify-center p-3 text-gray-300 hover:text-white hover:bg-gray-800 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-400"
        >
          {isDesktopOpen ? (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          )}
        </button>

        <button
          onClick={onNewConversation}
          aria-label="Criar nova conversa"
          className={`flex-1 items-center justify-center gap-2 px-4 py-3 text-sm font-medium border border-gray-700 rounded-lg hover:bg-gray-800 transition-colors focus:ring-2 focus:ring-gray-400 focus:outline-none ${isDesktopOpen ? 'flex' : 'flex md:hidden'}`}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Nova Conversa
        </button>
        
        <button 
          onClick={onClose} 
          className="md:hidden p-3 text-gray-400 hover:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-400"
          aria-label="Fechar menu"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <nav id="conversation-history" className={`flex-1 overflow-y-auto px-3 py-2 space-y-1 ${isDesktopOpen ? '' : 'md:hidden'}`} aria-label="Histórico de conversas">
        <h3 className="text-xs font-semibold text-gray-400 mb-3 px-2 uppercase tracking-wider">
          Histórico
        </h3>
        
        {error ? (
          <div className="px-2 text-center mt-4">
            <p className="text-sm text-red-400 mb-3" role="alert">{error}</p>
            <button onClick={onRetry} className="text-xs px-3 py-2 bg-gray-800 text-gray-300 rounded hover:bg-gray-700 w-full focus:ring-2 focus:ring-gray-400">
              Tentar novamente
            </button>
          </div>
        ) : isLoading ? (
          <p className="text-sm text-gray-500 px-2 animate-pulse" aria-busy="true">Carregando conversas...</p>
        ) : conversations.length === 0 ? (
          <p className="text-sm text-gray-500 px-2 italic">Nenhuma conversa ainda.</p>
        ) : (
          conversations.map((conv) => (
            <button
              key={conv.id}
              onClick={() => onSelectConversation(conv.id)}
              aria-current={currentConversationId === conv.id ? 'page' : undefined}
              className={`w-full text-left truncate px-3 py-3 rounded-lg text-sm transition-colors flex flex-col gap-1 focus:outline-none focus:ring-2 focus:ring-gray-400 ${
                currentConversationId === conv.id
                  ? 'bg-gray-800 text-white'
                  : 'text-gray-300 hover:bg-gray-800'
              }`}
            >
              <span className="truncate font-medium">{conv.title || 'Conversa sem título'}</span>
              <span className="text-[10px] text-gray-400">{formatDate(conv.created_at)}</span>
            </button>
          ))
        )}
      </nav>
    </aside>
  );
}