import { useMemo } from 'react';
import { Header } from './components/Header';
import { VideoPlayer } from './components/VideoPlayer';
import { StatusBar } from './components/StatusBar';
import { HealthPanel } from './components/HealthPanel';
import { useWebRTC } from './hooks/useWebRTC';
import { useHealthPolling } from './hooks/useHealthPolling';
import type { BackendConfig } from './types';

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
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', background: 'var(--bg-page)' }}>
      <Header />

      {/* Área principal — vídeo centralizado */}
      <main
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '24px 16px 16px',
          gap: 12,
        }}
      >
        {/* Wrapper do vídeo com borda de acento */}
        <div
          style={{
            position: 'relative',
            width: '100%',
            maxWidth: '960px',
            borderRadius: 8,
            overflow: 'hidden',
            border: '1px solid var(--border-subtle)',
            boxShadow: '0 4px 24px rgba(0, 0, 0, 0.18)',
          }}
        >
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

        {/* Barra de status e painel de saúde */}
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', justifyContent: 'center', width: '100%', maxWidth: 960 }}>
          <StatusBar connectionState={connectionState} streamStats={streamStats} />
          <HealthPanel health={health} healthError={healthError} />
        </div>
      </main>
    </div>
  );
}

export default App;
