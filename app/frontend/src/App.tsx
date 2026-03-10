import { useMemo } from 'react';
import { Layout, Row, Col } from 'antd';
import { Header } from './components/Header';
import { VideoPlayer } from './components/VideoPlayer';
import { StatusBar } from './components/StatusBar';
import { HealthPanel } from './components/HealthPanel';
import { useWebRTC } from './hooks/useWebRTC';
import { useHealthPolling } from './hooks/useHealthPolling';
import type { BackendConfig } from './types';
import styles from './App.module.css';

function resolveBackendConfig(): BackendConfig {
  const params = new URLSearchParams(window.location.search);
  const override = params.get('backend');
  return { url: override ?? window.location.origin };
}

function App() {
  const config = useMemo(resolveBackendConfig, []);
  const { videoRef, connectionState, streamStats } = useWebRTC(config);
  const { health, healthError } = useHealthPolling(config);

  const isReconnecting = connectionState === 'connecting' || connectionState === 'reconnecting';

  return (
    <Layout className={styles.root}>
      <Header />

      <Layout.Content className={styles.content}>
        {/* Wrapper do vídeo com borda de acento */}
        <div className={styles.videoWrapper}>
          <VideoPlayer videoRef={videoRef} />

          {connectionState !== 'connected' && (
            <div className={`video-overlay${isReconnecting ? ' video-overlay--reconnecting' : ''}`}>
              {connectionState === 'connecting' && 'Conectando…'}
              {connectionState === 'reconnecting' && 'Reconectando…'}
              {connectionState === 'failed' && 'Falha na conexão'}
              {connectionState === 'idle' && 'Aguardando…'}
              {connectionState === 'disconnected' && 'Desconectado'}
            </div>
          )}
        </div>

        {/* Barra de status e painel de saúde — responsivo */}
        <Row
          gutter={[8, 8]}
          justify="center"
          className={styles.bottomRow}
        >
          <Col xs={24} sm={24} md="auto">
            <StatusBar connectionState={connectionState} streamStats={streamStats} />
          </Col>
          <Col xs={24} sm={24} md="auto" className={styles.bottomColHealth}>
            <HealthPanel health={health} healthError={healthError} />
          </Col>
        </Row>
      </Layout.Content>
    </Layout>
  );
}

export default App;
