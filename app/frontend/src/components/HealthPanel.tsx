import type { HealthData } from '../types';

interface HealthPanelProps {
  health: HealthData | null;
  healthError: boolean;
}

function fmt(n: number, decimals = 1): string {
  return n.toFixed(decimals);
}

function fmtUptime(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}

export function HealthPanel({ health, healthError }: HealthPanelProps) {
  if (healthError) {
    return (
      <div className="health-panel">
        <span style={{ color: '#e53935', fontSize: '0.75rem' }}>Backend inacessível</span>
      </div>
    );
  }

  if (!health) {
    return (
      <div className="health-panel">
        <span style={{ color: 'var(--text-secondary)', fontSize: '0.75rem' }}>Carregando…</span>
      </div>
    );
  }

  const okColor = 'var(--brand-green)';
  const warnColor = '#f0a500';
  const errColor = '#e53935';

  return (
    <div className="health-panel">
      <Item
        label="Backend"
        value={health.status.toUpperCase()}
        color={health.status === 'ok' ? okColor : warnColor}
      />
      <Item
        label="ZMQ"
        value={health.zmq_connected ? 'ok' : 'offline'}
        color={health.zmq_connected ? okColor : errColor}
      />
      <Item label="Peers" value={String(health.peers_active)} />
      <Item
        label="FPS ZMQ"
        value={fmt(health.fps_recent)}
        color={health.fps_below_threshold ? warnColor : undefined}
      />
      <Item label="Frames" value={String(health.frames_received)} />
      <Item label="Uptime" value={fmtUptime(health.uptime_seconds)} />
    </div>
  );
}

function Item({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="health-item">
      <span className="health-item__label">{label}</span>
      <span className="health-item__value" style={color ? { color } : undefined}>
        {value}
      </span>
    </div>
  );
}
