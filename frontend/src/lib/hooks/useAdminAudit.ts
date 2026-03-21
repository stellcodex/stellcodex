"use client";

import * as React from "react";

import { getAdminAudit } from "@/lib/api/admin";
import { mapAdminAudit } from "@/lib/mappers/adminMappers";

export function useAdminAudit() {
  const [items, setItems] = React.useState<ReturnType<typeof mapAdminAudit>[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  const refresh = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setItems((await getAdminAudit()).map(mapAdminAudit));
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Admin audit data could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    void refresh();
  }, [refresh]);

  return { items, loading, error, refresh };
}
