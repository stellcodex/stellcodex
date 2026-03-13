"use client";

import { useCallback, useEffect, useState } from "react";
import { getAudit, getFailedJobs, getFiles, getQueues, getUsers } from "@/lib/api/admin";
import { mapAdminFiles, mapAudit, mapFailedJobs, mapQueues, mapUsers } from "@/lib/mappers/adminMappers";

export function useAdminQueues() {
  const [queues, setQueues] = useState<ReturnType<typeof mapQueues>>([]);
  const [failedJobs, setFailedJobs] = useState<ReturnType<typeof mapFailedJobs>>([]);
  const [audit, setAudit] = useState<ReturnType<typeof mapAudit>>([]);
  const [users, setUsers] = useState<ReturnType<typeof mapUsers>>([]);
  const [files, setFiles] = useState<ReturnType<typeof mapAdminFiles>>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [queuesPayload, failedPayload, auditPayload, usersPayload, filesPayload] = await Promise.all([
        getQueues(),
        getFailedJobs(),
        getAudit(),
        getUsers(),
        getFiles(),
      ]);
      setQueues(mapQueues(queuesPayload));
      setFailedJobs(mapFailedJobs(failedPayload));
      setAudit(mapAudit(auditPayload));
      setUsers(mapUsers(usersPayload));
      setFiles(mapAdminFiles(filesPayload));
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Admin queues could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { queues, failedJobs, audit, users, files, loading, error, refresh };
}
