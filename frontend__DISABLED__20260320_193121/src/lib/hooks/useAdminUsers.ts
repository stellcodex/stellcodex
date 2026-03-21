"use client";

import * as React from "react";

import { getAdminUsers } from "@/lib/api/admin";
import { mapAdminUser } from "@/lib/mappers/adminMappers";

export function useAdminUsers() {
  const [items, setItems] = React.useState<ReturnType<typeof mapAdminUser>[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  const refresh = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setItems((await getAdminUsers()).map(mapAdminUser));
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Admin user data could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    void refresh();
  }, [refresh]);

  return { items, loading, error, refresh };
}
