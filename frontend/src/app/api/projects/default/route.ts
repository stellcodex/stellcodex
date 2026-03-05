import { NextResponse } from "next/server";
import { apiBase, readErrorMessage, readPayload, upstreamHeaders } from "@/app/api/_lib/upstream";

export async function GET(req: Request) {
  let upstream: Response;
  try {
    upstream = await fetch(`${apiBase()}/projects`, {
      headers: upstreamHeaders(req),
      cache: "no-store",
    });
  } catch {
    return NextResponse.json({ error: "Upstream projects endpoint unreachable." }, { status: 502 });
  }

  const payload = await readPayload(upstream);
  if (!upstream.ok) {
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
    return NextResponse.json({ error: "No projects available upstream." }, { status: 404 });
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
