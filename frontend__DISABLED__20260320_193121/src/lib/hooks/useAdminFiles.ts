"use client";

import * as React from "react";

import { getAdminFiles } from "@/lib/api/admin";
import { mapAdminFile } from "@/lib/mappers/adminMappers";

export function useAdminFiles() {
  const [items, setItems] = React.useState<ReturnType<typeof mapAdminFile>[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  const refresh = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setItems((await getAdminFiles()).map(mapAdminFile));
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Admin file data could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    void refresh();
  }, [refresh]);

  return { items, loading, error, refresh };
}
