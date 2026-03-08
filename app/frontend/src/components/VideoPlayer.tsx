import { useCallback, useState } from 'react';
import type { RefObject } from 'react';

interface VideoPlayerProps {
  videoRef: RefObject<HTMLVideoElement | null>;
}

export function VideoPlayer({ videoRef }: VideoPlayerProps) {
  const [isFullscreen, setIsFullscreen] = useState(false);

  const toggleFullscreen = useCallback(() => {
    const el = videoRef.current;
    if (!el) return;

    if (!document.fullscreenElement) {
      el.requestFullscreen().catch(() => {/* navegador bloqueou */});
    } else {
      document.exitFullscreen();
    }
  }, [videoRef]);

  // Sincroniza o ícone com o estado real do fullscreen
  const onFullscreenChange = useCallback(() => {
    setIsFullscreen(!!document.fullscreenElement);
  }, []);

  return (
    <div
      style={{ position: 'relative', lineHeight: 0 }}
      onMouseEnter={(e) => {
        const btn = e.currentTarget.querySelector<HTMLButtonElement>('.fs-btn');
        if (btn) btn.style.opacity = '1';
      }}
      onMouseLeave={(e) => {
        const btn = e.currentTarget.querySelector<HTMLButtonElement>('.fs-btn');
        if (btn) btn.style.opacity = '0';
      }}
    >
      <video
        ref={videoRef}
        autoPlay
        muted
        playsInline
        onFullscreenChange={onFullscreenChange}
        style={{
          width: '100%',
          maxHeight: '100vh',
          objectFit: 'contain',
          background: '#000',
          display: 'block',
        }}
      />

      {/* Botão fullscreen — aparece ao passar o mouse */}
      <button
        className="fs-btn"
        onClick={toggleFullscreen}
        title={isFullscreen ? 'Sair do fullscreen' : 'Fullscreen'}
        style={{
          position: 'absolute',
          bottom: 12,
          right: 12,
          width: 36,
          height: 36,
          borderRadius: 6,
          border: '1px solid rgba(255,255,255,0.25)',
          background: 'rgba(0,0,0,0.55)',
          color: '#fff',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          opacity: 0,
          transition: 'opacity 0.18s ease, background 0.18s ease',
          backdropFilter: 'blur(4px)',
          padding: 0,
        }}
        onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(95,237,0,0.75)')}
        onMouseLeave={(e) => (e.currentTarget.style.background = 'rgba(0,0,0,0.55)')}
      >
        {isFullscreen ? (
          /* ícone "sair fullscreen" */
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="8 3 3 3 3 8"/>
            <polyline points="21 8 21 3 16 3"/>
            <polyline points="3 16 3 21 8 21"/>
            <polyline points="16 21 21 21 21 16"/>
          </svg>
        ) : (
          /* ícone "entrar fullscreen" */
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="15 3 21 3 21 9"/>
            <polyline points="9 21 3 21 3 15"/>
            <line x1="21" y1="3" x2="14" y2="10"/>
            <line x1="3" y1="21" x2="10" y2="14"/>
          </svg>
        )}
      </button>
    </div>
  );
}
