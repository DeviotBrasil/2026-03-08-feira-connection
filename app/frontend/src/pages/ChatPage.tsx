import { useRef, useEffect, type KeyboardEvent } from 'react';
import { Button, Empty, Input, Typography } from 'antd';
import { SendOutlined, ClearOutlined } from '@ant-design/icons';
import { useChat } from '../hooks/useChat';
import styles from './ChatPage.module.css';

interface ChatPageProps {
  backendUrl: string;
}

export function ChatPage({ backendUrl }: ChatPageProps) {
  const { messages, input, streaming, setInput, sendMessage, resetConversation } = useChat(backendUrl);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll para a última mensagem
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  function handleEnter(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  const hasOnlyWelcome = messages.length === 1 && messages[0].role === 'assistant';

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <Typography.Title level={4} style={{ margin: 0 }}>Chat IA</Typography.Title>
        <Button
          icon={<ClearOutlined />}
          onClick={resetConversation}
          disabled={streaming}
        >
          Nova Conversa
        </Button>
      </div>

      <div className={styles.messages} ref={scrollRef}>
        {hasOnlyWelcome ? (
          <>
            <div className={styles.assistantMsg}>
              <Typography.Text>{messages[0].content}</Typography.Text>
            </div>
            <Empty
              description="Digite uma mensagem para começar"
              style={{ marginTop: 32, opacity: 0.5 }}
            />
          </>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={msg.role === 'user' ? styles.userMsg : styles.assistantMsg}
            >
              <Typography.Text style={{ whiteSpace: 'pre-wrap' }}>
                {msg.content}
              </Typography.Text>
              {msg.streaming && <span className={styles.cursor}>▋</span>}
            </div>
          ))
        )}
      </div>

      <div className={styles.inputArea}>
        <Input.TextArea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleEnter}
          disabled={streaming}
          autoSize={{ minRows: 1, maxRows: 6 }}
          placeholder="Digite sua mensagem… (Enter para enviar, Shift+Enter para nova linha)"
          style={{ flex: 1 }}
        />
        <Button
          type="primary"
          icon={<SendOutlined />}
          onClick={sendMessage}
          disabled={!input.trim() || streaming}
          loading={streaming}
        >
          Enviar
        </Button>
      </div>
    </div>
  );
}
