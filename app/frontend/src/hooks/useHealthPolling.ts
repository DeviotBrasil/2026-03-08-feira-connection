import { useEffect, useRef, useState } from 'react';
import type { BackendConfig, HealthData } from '../types';

const POLL_INTERVAL_MS = 5000;

export function useHealthPolling(config: BackendConfig) {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [healthError, setHealthError] = useState(false);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;

    const poll = async () => {
      try {
        const res = await fetch(`${config.url}/health`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data: HealthData = await res.json();
        if (mountedRef.current) {
          setHealth(data);
          setHealthError(false);
        }
      } catch {
        if (mountedRef.current) setHealthError(true);
      }
    };

    poll();
    const id = setInterval(poll, POLL_INTERVAL_MS);
    return () => {
      mountedRef.current = false;
      clearInterval(id);
    };
  }, [config.url]);

  return { health, healthError };
}
