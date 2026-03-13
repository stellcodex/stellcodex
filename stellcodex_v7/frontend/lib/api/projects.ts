import { apiFetchJson } from "@/lib/api/client";

export async function getProjects() {
  return apiFetchJson("/projects");
}

export async function getProject(projectId: string) {
  return apiFetchJson(`/projects/${encodeURIComponent(projectId)}`);
}
