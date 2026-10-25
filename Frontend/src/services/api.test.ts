import { afterEach, describe, expect, it, vi } from 'vitest';
import { api } from './api';

describe('api.sendMessage streaming response', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('reads the conversation ID from stream metadata', async () => {
    const streamPayload = [
      JSON.stringify({
        conversation_id: 'conversation-123',
        tools_used: [],
      }),
      '\n|||\n',
      'Olá! Como posso ajudar?',
    ].join('');
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response(streamPayload)),
    );
    const onChunk = vi.fn();

    const result = await api.sendMessage(
      { message: 'Oi!' },
      onChunk,
    );

    expect(result).toEqual({
      conversation_id: 'conversation-123',
      response: 'Olá! Como posso ajudar?',
      tools_used: [],
    });
    expect(onChunk).toHaveBeenCalledWith('Olá! Como posso ajudar?');
  });
});
