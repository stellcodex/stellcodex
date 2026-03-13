"use client";

import { useCallback, useEffect, useState } from "react";
import { getHealth } from "@/lib/api/admin";

export function useAdminHealth() {
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = await getHealth();
      setData(payload as Record<string, unknown>);
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Admin health could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { data, loading, error, refresh };
}
