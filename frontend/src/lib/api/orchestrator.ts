import type {
  RawApprovalResponse,
  RawOrchestratorInputResponse,
  RawOrchestratorSession,
  RawRequiredInputs,
} from "@/lib/contracts/orchestrator";

import { apiJson } from "./fetch";
import { getAuthHeaders } from "./session";

export async function startOrchestrator(fileId: string) {
  return apiJson<RawOrchestratorSession>(`/orchestrator/start?file_id=${encodeURIComponent(fileId)}`, {
    method: "POST",
    headers: await getAuthHeaders(),
  });
}

export async function getDecision(params: { fileId?: string; sessionId?: string }) {
  const query = new URLSearchParams();
  if (params.fileId) query.set("file_id", params.fileId);
  if (params.sessionId) query.set("session_id", params.sessionId);
  return apiJson<RawOrchestratorSession>(`/orchestrator/decision?${query.toString()}`, {
    headers: await getAuthHeaders(),
  });
}

export async function getRequiredInputs(sessionId: string) {
  return apiJson<RawRequiredInputs>(`/orchestrator/required-inputs?session_id=${encodeURIComponent(sessionId)}`, {
    headers: await getAuthHeaders(),
  });
}

export async function submitOrchestratorInput(sessionId: string, key: string, value: string) {
  return apiJson<RawOrchestratorInputResponse>("/orchestrator/input", {
    method: "POST",
    headers: await getAuthHeaders({ headers: { "Content-Type": "application/json" } }),
    body: JSON.stringify({
      session_id: sessionId,
      key,
      value,
    }),
  });
}

export async function approveSession(sessionId: string, reason?: string) {
  return apiJson<RawApprovalResponse>(`/approvals/${encodeURIComponent(sessionId)}/approve`, {
    method: "POST",
    headers: await getAuthHeaders({ headers: { "Content-Type": "application/json" } }),
    body: JSON.stringify({ reason }),
  });
}

export async function rejectSession(sessionId: string, reason?: string) {
  return apiJson<RawApprovalResponse>(`/approvals/${encodeURIComponent(sessionId)}/reject`, {
    method: "POST",
    headers: await getAuthHeaders({ headers: { "Content-Type": "application/json" } }),
    body: JSON.stringify({ reason }),
  });
}
