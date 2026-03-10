import { useEffect, useMemo, useState } from 'react';
import { ConfigProvider, Layout, Row, Col } from 'antd';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import type { Page } from './components/Sidebar';
import { VideoPlayer } from './components/VideoPlayer';
import { StatusBar } from './components/StatusBar';
import { HealthPanel } from './components/HealthPanel';
import { ChatPage } from './pages/ChatPage';
import { useWebRTC } from './hooks/useWebRTC';
import { useHealthPolling } from './hooks/useHealthPolling';
import type { BackendConfig } from './types';
import { lightTheme, darkTheme } from './theme';
import styles from './App.module.css';

function resolveBackendConfig(): BackendConfig {
  const params = new URLSearchParams(window.location.search);
  const override = params.get('backend');
  return { url: override ?? window.location.origin };
}

function App() {
  const [isDark, setIsDark] = useState(false);
  const [activePage, setActivePage] = useState<Page>('camera');
  useEffect(() => {
    document.body.dataset.theme = isDark ? 'dark' : 'light';
  }, [isDark]);
  const config = useMemo(resolveBackendConfig, []);
  const { videoRef, connectionState, streamStats } = useWebRTC(config);
  const { health, healthError } = useHealthPolling(config);

  const isReconnecting = connectionState === 'connecting' || connectionState === 'reconnecting';

  return (
    <ConfigProvider theme={isDark ? darkTheme : lightTheme}>
    <Layout className={styles.root}>
      <Header isDark={isDark} onToggleTheme={() => setIsDark(d => !d)} />

      <Layout>
        <Sidebar isDark={isDark} activePage={activePage} onNavigate={setActivePage} />

        <Layout.Content className={styles.content}>
          {/* Câmera: sempre montada para o WebRTC não perder o stream */}
          <div style={{ display: activePage === 'camera' ? 'contents' : 'none' }}>
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
            <Row gutter={[8, 8]} justify="center" className={styles.bottomRow}>
              <Col xs={24} sm={24} md="auto">
                <StatusBar connectionState={connectionState} streamStats={streamStats} />
              </Col>
              <Col xs={24} sm={24} md="auto" className={styles.bottomColHealth}>
                <HealthPanel health={health} healthError={healthError} />
              </Col>
            </Row>
          </div>

          {activePage === 'chat' && (
            <div className={styles.chatWrapper}>
              <ChatPage backendUrl={config.url} />
            </div>
          )}
      </Layout.Content>
      </Layout>
    </Layout>
    </ConfigProvider>
  );
}

export default App;
