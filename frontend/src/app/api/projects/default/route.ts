import { NextResponse } from "next/server";
import { apiBase, readErrorMessage, readPayload, upstreamHeaders } from "@/app/api/_lib/upstream";

export async function GET(req: Request) {
  const fallback = NextResponse.json({ projectId: "default", name: "Default Project" });
  let upstream: Response;
  try {
    upstream = await fetch(`${apiBase()}/projects`, {
      headers: upstreamHeaders(req),
      cache: "no-store",
    });
  } catch {
    return fallback;
  }

  const payload = await readPayload(upstream);
  if (!upstream.ok) {
    if (upstream.status === 404 || upstream.status === 401 || upstream.status === 403) {
      return fallback;
    }
    return NextResponse.json(
      { error: readErrorMessage(payload, "Projeler yüklenemedi.") },
      { status: upstream.status }
    );
  }

  const projects = Array.isArray(payload) ? payload : [];
  const selected =
    projects.find((item) => item && typeof item === "object" && (item as { id?: unknown }).id === "default") ||
    projects[0] ||
    null;

  if (!selected || typeof selected !== "object") {
    return fallback;
  }

  const projectId =
    typeof (selected as { id?: unknown }).id === "string" && String((selected as { id: string }).id).trim()
      ? String((selected as { id: string }).id)
      : "default";
  const name =
    typeof (selected as { name?: unknown }).name === "string" && String((selected as { name: string }).name).trim()
      ? String((selected as { name: string }).name)
      : projectId === "default"
      ? "Default Project"
      : projectId;

  return NextResponse.json({ projectId, name });
}
