import { useState, useEffect, useCallback, useRef } from 'react';

const MAX_RETRIES = 3;
const RETRY_DELAY_MS = 2000;
const STALE_THRESHOLD_MS = 5 * 60 * 1000; // 5 minutes

/**
 * Generic fetch hook with retry logic and stale data detection.
 */
export function useApi(url, options = {}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isStale, setIsStale] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const lastFetchedAt = useRef(null);
  const retryTimer = useRef(null);

  const fetchData = useCallback(async (attempt = 0) => {
    // Only show loading on first attempt (preserve stale data on retries)
    if (attempt === 0) setLoading(true);
    setError(null);

    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      const json = await res.json();
      setData(json);
      setIsStale(false);
      setRetryCount(0);
      lastFetchedAt.current = Date.now();
    } catch (err) {
      if (attempt < MAX_RETRIES) {
        setRetryCount(attempt + 1);
        // If we have cached data, mark it stale instead of showing error
        if (data !== null) {
          setIsStale(true);
        }
        retryTimer.current = setTimeout(() => {
          fetchData(attempt + 1);
        }, RETRY_DELAY_MS * (attempt + 1)); // Exponential-ish backoff
      } else {
        setError(err.message);
        setRetryCount(0);
        if (data !== null) setIsStale(true);
      }
    } finally {
      if (attempt === 0 || attempt >= MAX_RETRIES) {
        setLoading(false);
      }
    }
  }, [url]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    fetchData();
    return () => {
      if (retryTimer.current) clearTimeout(retryTimer.current);
    };
  }, [fetchData]);

  // Check staleness periodically
  useEffect(() => {
    const interval = setInterval(() => {
      if (lastFetchedAt.current && Date.now() - lastFetchedAt.current > STALE_THRESHOLD_MS) {
        setIsStale(true);
      }
    }, 30000); // Check every 30s
    return () => clearInterval(interval);
  }, []);

  return { data, loading, error, isStale, retryCount, refetch: () => fetchData(0) };
}
