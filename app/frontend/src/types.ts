// ConnectionState — estados possíveis da RTCPeerConnection no frontend
export type ConnectionState =
  | 'idle'
  | 'connecting'
  | 'connected'
  | 'disconnected'
  | 'reconnecting'
  | 'failed';

// HealthData — espelha HealthStatus de webrtc-backend/models.py
export interface HealthData {
  status: 'ok' | 'degraded';
  zmq_connected: boolean;
  peers_active: number;
  fps_recent: number;
  fps_below_threshold: boolean;
  frames_received: number;
  frames_distributed: number;
  uptime_seconds: number;
}

// StreamStats — estatísticas medidas diretamente no elemento <video>
export interface StreamStats {
  fps: number;
  lastFrameAt: number | null;
}

// BackendConfig — resolvida uma vez no mount do App
export interface BackendConfig {
  url: string;
}
