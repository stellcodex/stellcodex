import { apiFetchJson } from "@/lib/api/client";

export async function approve(sessionId: string, note?: string) {
  return apiFetchJson(
    `/approvals/${encodeURIComponent(sessionId)}/approve`,
    {
      method: "POST",
      body: JSON.stringify({ note: note || null }),
    },
    { requireUser: true }
  );
}

export async function reject(sessionId: string, note?: string) {
  return apiFetchJson(
    `/approvals/${encodeURIComponent(sessionId)}/reject`,
    {
      method: "POST",
      body: JSON.stringify({ note: note || null }),
    },
    { requireUser: true }
  );
}
