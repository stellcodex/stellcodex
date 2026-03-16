import type { RawProject } from "@/lib/contracts/projects";

import { apiJson } from "./fetch";
import { getAuthHeaders } from "./session";

export async function listProjects() {
  return apiJson<RawProject[]>("/projects", {
    headers: await getAuthHeaders(),
  });
}

export async function getProject(projectId: string) {
  return apiJson<RawProject>(`/projects/${encodeURIComponent(projectId)}`, {
    headers: await getAuthHeaders(),
  });
}

export async function createProject(name: string) {
  return apiJson<RawProject>("/projects", {
    method: "POST",
    headers: await getAuthHeaders({ headers: { "Content-Type": "application/json" } }),
    body: JSON.stringify({ name }),
  });
}
