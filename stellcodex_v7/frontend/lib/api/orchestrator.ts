import { apiFetchJson } from "@/lib/api/client";

export async function startOrchestrator(fileId: string) {
  return apiFetchJson("/orchestrator/start", {
    method: "POST",
    body: JSON.stringify({ file_id: fileId }),
  });
}

export async function getSession(fileId: string) {
  return apiFetchJson(`/orchestrator/session?file_id=${encodeURIComponent(fileId)}`);
}

export async function advanceWorkflow(fileId: string, approve = false, note?: string) {
  return apiFetchJson("/orchestrator/advance", {
    method: "POST",
    body: JSON.stringify({ file_id: fileId, approve, note: note || null }),
  });
}

export async function getDecision(sessionId: string) {
  return apiFetchJson(`/orchestrator/decision?session_id=${encodeURIComponent(sessionId)}`);
}
