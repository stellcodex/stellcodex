export function isReadyStatus(status?: string | null) {
  const value = (status || "").toLowerCase();
  return value === "ready" || value === "succeeded" || value === "approved" || value === "share_ready";
}

export function isFailedStatus(status?: string | null) {
  return (status || "").toLowerCase() === "failed";
}

export function getViewerState(status?: string | null) {
  if (isFailedStatus(status)) return "failed" as const;
  if (isReadyStatus(status)) return "ready" as const;
  return "processing" as const;
}
