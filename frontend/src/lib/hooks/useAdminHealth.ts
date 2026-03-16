"use client";

import * as React from "react";

import { getAdminHealth } from "@/lib/api/admin";
import { mapAdminHealth } from "@/lib/mappers/adminMappers";

export function useAdminHealth() {
  const [items, setItems] = React.useState<ReturnType<typeof mapAdminHealth>>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  const refresh = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setItems(mapAdminHealth(await getAdminHealth()));
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Admin health data could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    void refresh();
  }, [refresh]);

  return { items, loading, error, refresh };
}
