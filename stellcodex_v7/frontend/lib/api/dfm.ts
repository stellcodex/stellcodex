import { apiFetchJson } from "@/lib/api/client";

export async function getDfmReport(fileId: string) {
  return apiFetchJson(`/dfm/report?file_id=${encodeURIComponent(fileId)}`);
}

export async function runDfm(fileId: string) {
  return apiFetchJson("/dfm/run", {
    method: "POST",
    body: JSON.stringify({ file_id: fileId }),
  });
}
