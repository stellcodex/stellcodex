"use client";

import { useEffect } from "react";

export function usePolling(callback: () => void, enabled: boolean, delayMs: number) {
  useEffect(() => {
    if (!enabled) return;
    const id = window.setInterval(callback, delayMs);
    return () => window.clearInterval(id);
  }, [callback, delayMs, enabled]);
}
