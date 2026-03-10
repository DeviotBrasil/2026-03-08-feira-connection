import { useCallback, useEffect, useState } from 'react';
import type { RefObject } from 'react';
import { Button, Tooltip } from 'antd';
import { FullscreenOutlined, FullscreenExitOutlined } from '@ant-design/icons';
import styles from './VideoPlayer.module.css';

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

  useEffect(() => {
    document.addEventListener('fullscreenchange', onFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', onFullscreenChange);
  }, [onFullscreenChange]);

  return (
    <div className={styles.wrapper}>
      <video
        ref={videoRef}
        autoPlay
        muted
        playsInline
        className={styles.video}
      />

      <Tooltip title={isFullscreen ? 'Sair do fullscreen' : 'Fullscreen'} placement="topRight">
        <Button
          className={styles.fullscreenBtn}
          type="text"
          size="small"
          icon={isFullscreen ? <FullscreenExitOutlined /> : <FullscreenOutlined />}
          onClick={toggleFullscreen}
        />
      </Tooltip>
    </div>
  );
}
