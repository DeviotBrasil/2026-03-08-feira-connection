import { Alert, Card, Skeleton } from 'antd';
import type { HealthData } from '../types';
import styles from './HealthPanel.module.css';

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

type DotStatus = 'ok' | 'warn' | 'err';

interface MetricItemProps {
  label: string;
  value: string | number;
  color?: string;
  dot?: DotStatus;
}

function MetricItem({ label, value, color, dot }: MetricItemProps) {
  return (
    <div className={styles.metricItem}>
      <span className={styles.metricLabel}>{label}</span>
      <span className={styles.metricValue} style={color ? { color } : undefined}>
        {dot && <span className={`${styles.dot} ${styles[`dot${dot.charAt(0).toUpperCase() + dot.slice(1)}`]}`} />}
        {value}
      </span>
    </div>
  );
}

export function HealthPanel({ health, healthError }: HealthPanelProps) {
  if (healthError) {
    return (
      <Alert
        type="error"
        message="Backend inacessível"
        showIcon
        className={styles.errorAlert}
      />
    );
  }

  if (!health) {
    return (
      <Card size="small" className={styles.panel}>
        <Skeleton active paragraph={{ rows: 1 }} title={false} />
      </Card>
    );
  }

  const okColor = '#5FED00';
  const warnColor = '#faad14';
  const errColor = '#ff4d4f';

  return (
    <Card size="small" className={styles.panel}>
      <div className={styles.metricsRow}>
        <MetricItem
          label="Backend"
          value={health.status.toUpperCase()}
          color={health.status === 'ok' ? okColor : warnColor}
          dot={health.status === 'ok' ? 'ok' : 'warn'}
        />
        <MetricItem
          label="ZMQ"
          value={health.zmq_connected ? 'OK' : 'OFFLINE'}
          color={health.zmq_connected ? okColor : errColor}
          dot={health.zmq_connected ? 'ok' : 'err'}
        />
        <MetricItem
          label="Peers"
          value={health.peers_active}
        />
        <MetricItem
          label="FPS"
          value={fmt(health.fps_recent)}
          color={health.fps_below_threshold ? warnColor : okColor}
        />
        <MetricItem
          label="Frames"
          value={health.frames_received.toLocaleString()}
        />
        <MetricItem
          label="Uptime"
          value={fmtUptime(health.uptime_seconds)}
        />
      </div>
    </Card>
  );
}
