import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom/vitest';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import App from './App';
import { api } from './services/api';
import { ChatMessage } from './components/ChatMessage';

// 1. MOCK DA API: Impede que o frontend faça chamadas HTTP reais
vi.mock('./services/api', () => ({
  api: {
    getConversations: vi.fn(),
    getConversationHistory: vi.fn(),
    deleteConversation: vi.fn(),
    sendMessage: vi.fn(),
  }
}));

function CurrentRoute() {
  const location = useLocation();
  return <span data-testid="current-route">{location.pathname}</span>;
}

function renderApp(initialPath = '/') {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route path="/:conversationId?" element={<><App /><CurrentRoute /></>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('Integração do App (Frontend)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('1. Deve renderizar a sidebar e listar o histórico mockado', async () => {
    (api.getConversations as any).mockResolvedValue([
      { id: 'conv-1', title: 'Minha primeira dúvida', created_at: new Date().toISOString() }
    ]);

    renderApp();

    expect(api.getConversations).toHaveBeenCalledTimes(1);
    expect(await screen.findByText('Minha primeira dúvida')).toBeInTheDocument();
  });

  it('ordena e mostra a data da última atualização da conversa', async () => {
    vi.mocked(api.getConversations).mockResolvedValue([
      {
        id: 'old-conversation',
        title: 'Conversa atualizada recentemente',
        created_at: '2026-10-01T12:00:00.000Z',
        updated_at: '2026-10-03T12:00:00.000Z',
      },
      {
        id: 'new-conversation',
        title: 'Conversa criada depois',
        created_at: '2026-10-02T12:00:00.000Z',
        updated_at: '2026-10-02T12:00:00.000Z',
      },
    ]);

    renderApp();

    const conversationButtons = await screen.findAllByRole('button', { name: /Abrir conversa/ });
    expect(conversationButtons[0]).toHaveAccessibleName('Abrir conversa Conversa atualizada recentemente');
    expect(screen.getByText('03/10/2026')).toBeInTheDocument();
  });

  it('deve recolher e expandir a sidebar no desktop', async () => {
    vi.mocked(api.getConversations).mockResolvedValue([]);

    renderApp();

    const sidebar = screen.getByLabelText('Menu Lateral');
    expect(sidebar).toHaveClass('md:w-64');

    fireEvent.click(screen.getByRole('button', { name: 'Recolher menu de conversas' }));
    expect(sidebar).toHaveClass('md:w-14');
    expect(screen.getByRole('button', { name: 'Expandir menu de conversas' })).toHaveAttribute('aria-expanded', 'false');
    expect(sidebar.querySelector('nav')).toHaveClass('md:hidden');

    fireEvent.click(screen.getByRole('button', { name: 'Expandir menu de conversas' }));
    expect(sidebar).toHaveClass('md:w-64');
    expect(sidebar.querySelector('nav')).not.toHaveClass('md:hidden');
  });

  it('2. Deve selecionar uma conversa do histórico e alinhar mensagens visualmente', async () => {
    (api.getConversations as any).mockResolvedValue([{ id: 'conv-1', title: 'Dúvida', created_at: new Date().toISOString() }]);
    
    (api.getConversationHistory as any).mockResolvedValue({
      messages: [
        { id: 'msg-1', role: 'user', content: 'Como centralizar uma div?' },
        { id: 'msg-2', role: 'assistant', content: 'Use flexbox e justify-center.' }
      ]
    });

    renderApp();
    
    // Seleciona especificamente o BOTÃO da conversa na sidebar
    const convButton = await screen.findByRole('button', { name: /Abrir conversa Dúvida/i });
    fireEvent.click(convButton);
    expect(screen.getByTestId('current-route')).toHaveTextContent('/conv-1');

    const userMsg = await screen.findByText('Como centralizar uma div?');
    const botMsg = await screen.findByText('Use flexbox e justify-center.');

    expect(userMsg).toBeInTheDocument();
    expect(botMsg).toBeInTheDocument();

    // VALIDAÇÃO VISUAL (Alinhamento)
    expect(userMsg.closest('.flex')).toHaveClass('justify-end'); // Usuário à direita
    expect(botMsg.closest('.flex')).toHaveClass('justify-start'); // Agente à esquerda
  });

  it('deve voltar para a rota sem ID ao iniciar uma nova conversa', async () => {
    (api.getConversations as any).mockResolvedValue([
      { id: 'conv-1', title: 'Conversa existente', created_at: new Date().toISOString() }
    ]);
    (api.getConversationHistory as any).mockResolvedValue({ messages: [] });

    renderApp('/conv-1');
    expect(await screen.findByTestId('current-route')).toHaveTextContent('/conv-1');

    fireEvent.click(screen.getByRole('button', { name: /nova conversa/i }));
    expect(screen.getByTestId('current-route')).toHaveTextContent('/');
  });

  it('3. Deve limpar o contexto ao clicar em "Nova Conversa"', async () => {
    (api.getConversations as any).mockResolvedValue([]);
    renderApp();

    // CORREÇÃO: Busca especificamente pelo BOTÃO para não conflitar com o Header
    const btnNovaConversa = screen.getByRole('button', { name: /nova conversa/i });
    fireEvent.click(btnNovaConversa);

    expect(await screen.findByText('Como posso ajudar hoje?')).toBeInTheDocument();
  });

  it('4. Deve enviar mensagem SEM conversation_id em uma nova conversa', async () => {
    const user = userEvent.setup();
    (api.getConversations as any).mockResolvedValue([]);
    (api.sendMessage as any).mockResolvedValue({
      response: 'Olá, sou o assistente!',
      conversation_id: 'nova-conv-123'
    });
    vi.mocked(api.getConversationHistory).mockResolvedValue({
      id: 'nova-conv-123',
      title: 'Nova conversa',
      created_at: new Date().toISOString(),
      messages: [{ id: 'msg-1', role: 'assistant', content: 'Olá, sou o assistente!' }],
    });

    renderApp();

    const input = screen.getByLabelText('Campo de entrada de texto');
    
    // Garante que o input não está desabilitado antes de digitar
    await waitFor(() => expect(input).not.toBeDisabled());

    await user.type(input, 'Oi!');
    
    const sendButton = screen.getByRole('button', { name: /enviar mensagem/i });
    await user.click(sendButton);

    await waitFor(() => {
      expect(api.sendMessage).toHaveBeenCalledWith({
        message: 'Oi!',
        conversation_id: null
      }, expect.any(Function));
    });

    expect(await screen.findByText('Olá, sou o assistente!')).toBeInTheDocument();
    await waitFor(() => expect(screen.getByTestId('current-route')).toHaveTextContent('/nova-conv-123'));
  });

  it('5. Deve enviar mensagem COM conversation_id ao estar em uma conversa existente', async () => {
    const user = userEvent.setup();
    
    (api.getConversations as any).mockResolvedValue([{ id: 'conv-existente', title: 'Chat', created_at: new Date().toISOString() }]);
    (api.getConversationHistory as any).mockResolvedValue({ messages: [] });
    (api.sendMessage as any).mockResolvedValue({ response: 'Entendido.', conversation_id: 'conv-existente' });

    renderApp();
    
    // Abre a conversa
    const convButton = await screen.findByRole('button', { name: /Abrir conversa Chat/i });
    fireEvent.click(convButton);

    const input = screen.getByLabelText('Campo de entrada de texto');

    // CORREÇÃO: Espera o carregamento do histórico terminar para o input ficar habilitado
    await waitFor(() => expect(input).not.toBeDisabled());

    await user.type(input, 'Continuando assunto...');

    const sendButton = screen.getByRole('button', { name: /enviar mensagem/i });
    await user.click(sendButton);

    await waitFor(() => {
      expect(api.sendMessage).toHaveBeenCalledWith({
        message: 'Continuando assunto...',
        conversation_id: 'conv-existente'
      }, expect.any(Function));
    });
  });

  it('6. Deve tratar erros da API exibindo estados amigáveis e botão Retry', async () => {
    // Silencia temporariamente o console.error para não poluir o terminal durante o teste de erro
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    (api.getConversations as any).mockRejectedValue(new Error('Network Error'));

    renderApp();

    expect(await screen.findByText('Não foi possível carregar o histórico.')).toBeInTheDocument();
    
    const retryButton = screen.getByRole('button', { name: /tentar novamente/i });
    expect(retryButton).toBeInTheDocument();

    (api.getConversations as any).mockResolvedValue([{ id: '1', title: 'Voltou a funcionar', created_at: new Date().toISOString() }]);
    
    fireEvent.click(retryButton);

    expect(await screen.findByText('Voltou a funcionar')).toBeInTheDocument();

    consoleSpy.mockRestore();
  });

  it('abre modal de exclusão, permite cancelar e exclui após confirmação', async () => {
    vi.mocked(api.getConversations).mockResolvedValue([
      { id: 'conv-1', title: 'Conversa teste', created_at: new Date().toISOString() },
    ]);
    vi.mocked(api.getConversationHistory).mockResolvedValue({ messages: [] } as any);
    vi.mocked(api.deleteConversation).mockResolvedValue(undefined);

    renderApp('/conv-1');

    const deleteButton = await screen.findByRole('button', {
      name: 'Excluir conversa Conversa teste',
    });
    expect(deleteButton).toHaveClass('hover:text-red-500');

    fireEvent.click(deleteButton);
    expect(screen.getByRole('dialog')).toHaveTextContent('Deseja excluir a conversa?');
    expect(api.deleteConversation).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: 'Cancelar' }));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(api.deleteConversation).not.toHaveBeenCalled();

    fireEvent.click(deleteButton);
    fireEvent.click(screen.getByRole('button', { name: 'Confirmar' }));

    await waitFor(() => expect(api.deleteConversation).toHaveBeenCalledWith('conv-1'));
    expect(await screen.findByTestId('current-route')).toHaveTextContent('/');
    expect(screen.queryByText('Conversa teste')).not.toBeInTheDocument();
  });
});

describe('Renderização de mensagens', () => {
  it('formata espaços como separadores de milhar em respostas do assistente', () => {
    render(
      <ChatMessage
        content={'Valores: 50\u202f000,00 e 1 000,00; código 123 4567.'}
        role="assistant"
      />,
    );

    expect(screen.getByText('Valores: 50.000,00 e 1.000,00; código 123 4567.')).toBeInTheDocument();
  });

  it('renderiza listas HTML como elementos e mantém HTML perigoso inerte', () => {
    const content = '<ul><li>Nível de risco:ALTO</li><li>Dia máximo de atraso: 35 dias (classificado como atraso crítico).</li></ul><img src="x" onerror="alert(1)" />';

    const { container } = render(<ChatMessage content={content} role="assistant" />);

    expect(screen.getAllByRole('listitem')).toHaveLength(2);
    expect(screen.getByText('Nível de risco:ALTO')).toBeInTheDocument();
    expect(container.querySelector('img')).not.toHaveAttribute('onerror');
  });
});