"use client";

import * as React from "react";

import { getAdminFailedJobs, getAdminQueues } from "@/lib/api/admin";
import { mapAdminFailedJob, mapAdminQueue } from "@/lib/mappers/adminMappers";

export function useAdminQueues() {
  const [queues, setQueues] = React.useState<ReturnType<typeof mapAdminQueue>[]>([]);
  const [failedJobs, setFailedJobs] = React.useState<ReturnType<typeof mapAdminFailedJob>[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  const refresh = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [queueRows, failedRows] = await Promise.all([getAdminQueues(), getAdminFailedJobs()]);
      setQueues(queueRows.map(mapAdminQueue));
      setFailedJobs(failedRows.map(mapAdminFailedJob));
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Admin queue data could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    void refresh();
  }, [refresh]);

  return { queues, failedJobs, loading, error, refresh };
}
