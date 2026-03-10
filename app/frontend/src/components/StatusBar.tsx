import { Tag, Typography } from 'antd';
import type { ConnectionState, StreamStats } from '../types';
import styles from './StatusBar.module.css';

interface StatusBarProps {
  connectionState: ConnectionState;
  streamStats: StreamStats;
}

const STATE_LABEL: Record<ConnectionState, string> = {
  idle: 'Aguardando',
  connecting: 'Conectando',
  connected: 'Conectado',
  disconnected: 'Desconectado',
  reconnecting: 'Reconectando',
  failed: 'Falha',
};

type TagColor = 'default' | 'processing' | 'success' | 'error';

const STATE_TAG_COLOR: Record<ConnectionState, TagColor> = {
  idle: 'default',
  connecting: 'processing',
  connected: 'success',
  disconnected: 'default',
  reconnecting: 'processing',
  failed: 'error',
};

export function StatusBar({ connectionState, streamStats }: StatusBarProps) {
  return (
    <div className={styles.bar}>
      <Tag color={STATE_TAG_COLOR[connectionState]}>
        {STATE_LABEL[connectionState]}
      </Tag>

      {connectionState === 'connected' && streamStats.fps > 0 && (
        <Typography.Text className={styles.fps}>
          {streamStats.fps} fps
        </Typography.Text>
      )}
    </div>
  );
}
