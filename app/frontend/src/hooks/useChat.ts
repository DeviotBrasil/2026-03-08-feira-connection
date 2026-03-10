import { useCallback, useRef, useState } from 'react';
import { message as antMessage } from 'antd';
import type { ChatMessage, ChatChunk } from '../types';

function makeId(): string {
  return crypto.randomUUID();
}

const WELCOME_MESSAGE: ChatMessage = {
  id: makeId(),
  role: 'assistant',
  content: 'Olá! Sou o assistente de IA da demonstração. Como posso ajudar?',
  timestamp: Date.now(),
};

interface UseChatReturn {
  messages: ChatMessage[];
  input: string;
  streaming: boolean;
  setInput: (value: string) => void;
  sendMessage: () => Promise<void>;
  resetConversation: () => void;
}

export function useChat(backendUrl: string): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME_MESSAGE]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);

  const abortControllerRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(async () => {
    const trimmed = input.trim();
    if (!trimmed || streaming) return;

    // Histórico completo para enviar ao backend (exclui a mensagem de boas-vindas do sistema)
    const userMsg: ChatMessage = {
      id: makeId(),
      role: 'user',
      content: trimmed,
      timestamp: Date.now(),
    };

    const placeholderId = makeId();
    const placeholder: ChatMessage = {
      id: placeholderId,
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
      streaming: true,
    };

    setMessages((prev) => [...prev, userMsg, placeholder]);
    setInput('');
    setStreaming(true);

    // Construir histórico completo (sem a mensagem de boas-vindas inicial que é somente UI)
    const history: { role: 'user' | 'assistant'; content: string }[] = messages
      .filter((m) => m.id !== WELCOME_MESSAGE.id)
      .map((m) => ({ role: m.role, content: m.content }));

    history.push({ role: 'user', content: trimmed });

    const controller = new AbortController();
    abortControllerRef.current = controller;

    let receivedAnyChunk = false;

    try {
      const response = await fetch(`${backendUrl}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: history }),
        signal: controller.signal,
      });

      if (!response.ok) {
        antMessage.error(`Erro no servidor: ${response.status}`);
        setMessages((prev) => prev.filter((m) => m.id !== placeholderId));
        setStreaming(false);
        return;
      }

      const reader = response.body?.getReader();
      if (!reader) {
        antMessage.error('Resposta inválida do servidor.');
        setMessages((prev) => prev.filter((m) => m.id !== placeholderId));
        setStreaming(false);
        return;
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Processar eventos SSE: "data: {...}\n\n"
        const parts = buffer.split('\n\n');
        buffer = parts.pop() ?? '';

        for (const part of parts) {
          const line = part.trim();
          if (!line.startsWith('data:')) continue;

          const json = line.slice('data:'.length).trim();
          if (!json) continue;

          const chunk: ChatChunk = JSON.parse(json);

          if (chunk.error) {
            antMessage.error(chunk.error);
            setMessages((prev) =>
              prev.map((m) =>
                m.id === placeholderId ? { ...m, streaming: false } : m
              )
            );
            setStreaming(false);
            return;
          }

          receivedAnyChunk = true;

          setMessages((prev) =>
            prev.map((m) =>
              m.id === placeholderId
                ? { ...m, content: m.content + chunk.content, streaming: !chunk.done }
                : m
            )
          );

          if (chunk.done) {
            setStreaming(false);
            return;
          }
        }
      }

      // Stream encerrado sem chunk done — marcar mensagem como não-streaming
      setMessages((prev) =>
        prev.map((m) =>
          m.id === placeholderId ? { ...m, streaming: false } : m
        )
      );
      setStreaming(false);
    } catch (err) {
      if ((err as Error).name === 'AbortError') return;

      // TypeError: falha de rede (backend down, offline)
      antMessage.error('Não foi possível conectar ao servidor. Verifique se o backend está rodando.');

      setMessages((prev) => {
        if (!receivedAnyChunk) {
          return prev.filter((m) => m.id !== placeholderId);
        }
        return prev.map((m) =>
          m.id === placeholderId ? { ...m, streaming: false } : m
        );
      });
      setStreaming(false);
    }
  }, [input, streaming, messages, backendUrl]);

  const resetConversation = useCallback(() => {
    // Cancelar fetch em andamento se houver
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setStreaming(false);
    setInput('');
    setMessages([{ ...WELCOME_MESSAGE, id: makeId(), timestamp: Date.now() }]);
  }, []);

  return { messages, input, streaming, setInput, sendMessage, resetConversation };
}
