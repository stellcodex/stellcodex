import type { RawDfmReport } from "@/lib/contracts/dfm";

import { apiJson } from "./fetch";
import { getAuthHeaders } from "./session";

export async function getDfmReport(fileId: string) {
  return apiJson<RawDfmReport>(`/dfm/report?file_id=${encodeURIComponent(fileId)}`, {
    headers: await getAuthHeaders(),
  });
}
