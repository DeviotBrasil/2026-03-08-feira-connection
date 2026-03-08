import type { ConnectionState, StreamStats } from '../types';

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

const STATE_COLOR: Record<ConnectionState, string> = {
  idle: '#555',
  connecting: 'var(--brand-green)',
  connected: 'var(--brand-green)',
  disconnected: '#555',
  reconnecting: 'var(--brand-green)',
  failed: '#e53935',
};

export function StatusBar({ connectionState, streamStats }: StatusBarProps) {
  const isAnimated =
    connectionState === 'reconnecting' || connectionState === 'connecting';

  return (
    <div className="status-bar">
      <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
        {isAnimated ? (
          <span
            className="status-dot status-dot--spin"
            style={{ width: 9, height: 9 }}
          />
        ) : (
          <span
            className="status-dot"
            style={{ background: STATE_COLOR[connectionState] }}
          />
        )}
        <span style={{ color: 'var(--text-primary)' }}>
          {STATE_LABEL[connectionState]}
        </span>
      </div>

      {connectionState === 'connected' && streamStats.fps > 0 && (
        <span style={{ color: 'var(--brand-green)', fontWeight: 600 }}>
          {streamStats.fps} fps
        </span>
      )}
    </div>
  );
}
