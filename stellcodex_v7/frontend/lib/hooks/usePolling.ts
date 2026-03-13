"use client";

import { useEffect, useRef } from "react";

export function usePolling(callback: () => void, enabled: boolean, delayMs: number) {
  const callbackRef = useRef(callback);

  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  useEffect(() => {
    if (!enabled || delayMs <= 0) return;
    const id = window.setInterval(() => callbackRef.current(), delayMs);
    return () => window.clearInterval(id);
  }, [delayMs, enabled]);
}
