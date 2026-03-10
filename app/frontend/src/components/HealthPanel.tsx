import { Alert, Badge, Card, Skeleton, Statistic } from 'antd';
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
    <Card
      size="small"
      className={styles.panel}
    >
      <div className={styles.metricsRow}>
        <div className={styles.metricItem}>
          <Badge
            status={health.status === 'ok' ? 'success' : 'warning'}
            text={
              <Statistic
                title="Backend"
                value={health.status.toUpperCase()}
                valueStyle={{ color: health.status === 'ok' ? okColor : warnColor, fontSize: '0.85rem' }}
              />
            }
          />
        </div>
        <div className={styles.metricItem}>
          <Statistic
            title="ZMQ"
            value={health.zmq_connected ? 'ok' : 'offline'}
            valueStyle={{ color: health.zmq_connected ? okColor : errColor, fontSize: '0.85rem' }}
          />
        </div>
        <div className={styles.metricItem}>
          <Statistic
            title="Peers"
            value={health.peers_active}
            valueStyle={{ fontSize: '0.85rem' }}
          />
        </div>
        <div className={styles.metricItem}>
          <Statistic
            title="FPS ZMQ"
            value={fmt(health.fps_recent)}
            valueStyle={{ color: health.fps_below_threshold ? warnColor : okColor, fontSize: '0.85rem' }}
          />
        </div>
        <div className={styles.metricItem}>
          <Statistic
            title="Frames"
            value={health.frames_received}
            valueStyle={{ fontSize: '0.85rem' }}
          />
        </div>
        <div className={styles.metricItem}>
          <Statistic
            title="Uptime"
            value={fmtUptime(health.uptime_seconds)}
            valueStyle={{ fontSize: '0.85rem' }}
          />
        </div>
      </div>
    </Card>
  );
}
