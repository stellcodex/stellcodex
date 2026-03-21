"use client";

import * as React from "react";

export interface UsePollingOptions {
  enabled: boolean;
  intervalMs: number;
  callback: () => void | Promise<void>;
}

export function usePolling({ callback, enabled, intervalMs }: UsePollingOptions) {
  const onTick = React.useEffectEvent(callback);

  React.useEffect(() => {
    if (!enabled) return;
    const interval = window.setInterval(() => {
      void onTick();
    }, intervalMs);
    return () => window.clearInterval(interval);
  }, [enabled, intervalMs]);
}
