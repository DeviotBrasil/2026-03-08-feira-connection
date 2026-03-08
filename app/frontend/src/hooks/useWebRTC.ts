import { useCallback, useEffect, useRef, useState } from 'react';
import type { BackendConfig, ConnectionState, StreamStats } from '../types';

const BACKOFF_STEPS_MS = [2000, 4000, 8000, 15000];

export function useWebRTC(config: BackendConfig) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const pcRef = useRef<RTCPeerConnection | null>(null);
  const mountedRef = useRef(true);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const backoffIndexRef = useRef(0);

  const [connectionState, setConnectionState] = useState<ConnectionState>('idle');
  const [streamStats, setStreamStats] = useState<StreamStats>({ fps: 0, lastFrameAt: null });

  const closePeer = useCallback(() => {
    const pc = pcRef.current;
    if (!pc) return;
    // Prevenir callbacks zombie antes do close
    pc.onconnectionstatechange = null;
    pc.ontrack = null;
    pc.onicecandidate = null;
    pc.getReceivers().forEach((r) => r.track?.stop());
    pc.getTransceivers().forEach((t) => { try { t.stop(); } catch { /* já parado */ } });
    pc.close();
    pcRef.current = null;
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  }, []);

  const connect = useCallback(async (isReconnect = false) => {
    if (!mountedRef.current) return;
    closePeer();
    setConnectionState(isReconnect ? 'reconnecting' : 'connecting');

    let cancelled = false;
    const pc = new RTCPeerConnection({ iceServers: [] });
    pcRef.current = pc;

    pc.ontrack = (event) => {
      if (cancelled || !videoRef.current) return;
      videoRef.current.srcObject = event.streams[0] ?? null;
    };

    pc.onconnectionstatechange = () => {
      if (cancelled || !mountedRef.current) return;
      const state = pc.connectionState;
      if (state === 'connected') {
        backoffIndexRef.current = 0;
        setConnectionState('connected');
      } else if (state === 'failed') {
        cancelled = true;
        closePeer();
        scheduleReconnect();
      }
    };

    pc.addTransceiver('video', { direction: 'recvonly' });

    try {
      const offer = await pc.createOffer();
      if (cancelled || !mountedRef.current) { pc.close(); return; }
      await pc.setLocalDescription(offer);

      const res = await fetch(`${config.url}/offer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sdp: pc.localDescription!.sdp, type: pc.localDescription!.type }),
      });
      if (cancelled || !mountedRef.current) { pc.close(); return; }
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const answer: RTCSessionDescriptionInit = await res.json();
      await pc.setRemoteDescription(answer);
    } catch {
      if (!cancelled) {
        cancelled = true;
        closePeer();
        if (mountedRef.current) scheduleReconnect();
      }
    }
  }, [config.url, closePeer]); // eslint-disable-line react-hooks/exhaustive-deps

  const scheduleReconnect = useCallback(() => {
    if (!mountedRef.current) return;
    setConnectionState('reconnecting');
    const delay = BACKOFF_STEPS_MS[Math.min(backoffIndexRef.current, BACKOFF_STEPS_MS.length - 1)];
    backoffIndexRef.current = Math.min(backoffIndexRef.current + 1, BACKOFF_STEPS_MS.length - 1);
    reconnectTimerRef.current = setTimeout(() => {
      if (mountedRef.current) connect(true);
    }, delay);
  }, [connect]);

  // Iniciar conexão ao montar
  useEffect(() => {
    mountedRef.current = true;
    connect(false);
    return () => {
      mountedRef.current = false;
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      closePeer();
      setConnectionState('disconnected');
    };
  }, [connect, closePeer]);

  // Medir FPS via requestVideoFrameCallback (com fallback para rAF)
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    let rafId: number | null = null;
    let lastTs = 0;
    let frameCount = 0;
    let intervalId: ReturnType<typeof setInterval> | null = null;

    const hasRVFC = 'requestVideoFrameCallback' in HTMLVideoElement.prototype;
    if (hasRVFC) {
      const onFrame = (_now: DOMHighResTimeStamp, meta: { mediaTime: number }) => {
        const now = meta.mediaTime * 1000;
        if (lastTs > 0) frameCount++;
        lastTs = now;
        if (mountedRef.current) {
          rafId = (video as HTMLVideoElement & { requestVideoFrameCallback: (cb: FrameRequestCallback) => number })
            .requestVideoFrameCallback(onFrame as FrameRequestCallback);
        }
      };
      rafId = (video as HTMLVideoElement & { requestVideoFrameCallback: (cb: FrameRequestCallback) => number })
        .requestVideoFrameCallback(onFrame as FrameRequestCallback);
      intervalId = setInterval(() => {
        if (mountedRef.current) {
          setStreamStats({ fps: frameCount, lastFrameAt: frameCount > 0 ? Date.now() : null });
        }
        frameCount = 0;
      }, 1000);
    }

    return () => {
      if (rafId !== null && hasRVFC) {
        (video as HTMLVideoElement & { cancelVideoFrameCallback: (id: number) => void })
          .cancelVideoFrameCallback(rafId);
      }
      if (intervalId) clearInterval(intervalId);
    };
  }, []);

  return { videoRef, connectionState, streamStats };
}
