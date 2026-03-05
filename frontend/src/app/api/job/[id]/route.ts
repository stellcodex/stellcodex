import { NextResponse } from "next/server";
import {
  apiBase,
  mapLegacyProgress,
  mapLegacyStage,
  mapLegacyStatusFromJob,
  mapLegacyStatusFromState,
  readErrorMessage,
  readPayload,
  upstreamHeaders,
} from "@/app/api/_lib/upstream";

function nowIso() {
  return new Date().toISOString();
}

async function resolveFileStatus(req: Request, fileId: string) {
  const statusRes = await fetch(`${apiBase()}/files/${encodeURIComponent(fileId)}/status`, {
    headers: upstreamHeaders(req),
    cache: "no-store",
  });
  const statusPayload = await readPayload(statusRes);
  if (!statusRes.ok) {
    return NextResponse.json(
      { error: readErrorMessage(statusPayload, "Job bulunamadı.") },
      { status: statusRes.status }
    );
  }

  const payload =
    statusPayload && typeof statusPayload === "object" ? (statusPayload as Record<string, unknown>) : {};
  const status = mapLegacyStatusFromState(payload.state);
  const stage = mapLegacyStage(payload.stage, payload.state);
  const progress = mapLegacyProgress(payload.progress_percent, payload.state);

  return NextResponse.json({
    id: `file:${fileId}`,
    fileId,
    status,
    stage,
    progress,
    error: null,
    createdAt: nowIso(),
    updatedAt: nowIso(),
  });
}

export async function GET(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  if (id.startsWith("file:")) {
    const fileId = id.slice("file:".length).trim();
    if (!fileId) return NextResponse.json({ error: "Geçersiz job id." }, { status: 400 });
    return resolveFileStatus(req, fileId);
  }

  const upstream = await fetch(`${apiBase()}/jobs/${encodeURIComponent(id)}`, {
    headers: upstreamHeaders(req),
    cache: "no-store",
  });
  const payload = await readPayload(upstream);
  if (!upstream.ok) {
    return NextResponse.json(
      { error: readErrorMessage(payload, "Job bulunamadı.") },
      { status: upstream.status }
    );
  }

  const body = payload && typeof payload === "object" ? (payload as Record<string, unknown>) : {};
  const status = mapLegacyStatusFromJob(body.status);
  const stage = mapLegacyStage((body.meta as Record<string, unknown> | null)?.stage, body.status);
  const progress = mapLegacyProgress((body.meta as Record<string, unknown> | null)?.progress_percent, body.status);
  const fileId =
    body.meta && typeof body.meta === "object" && typeof (body.meta as { file_id?: unknown }).file_id === "string"
      ? String((body.meta as { file_id: string }).file_id)
      : "";

  return NextResponse.json({
    id: typeof body.job_id === "string" ? body.job_id : id,
    fileId,
    status,
    stage,
    progress,
    error: typeof body.error === "string" ? body.error : null,
    createdAt: typeof body.enqueued_at === "string" ? body.enqueued_at : nowIso(),
    updatedAt: nowIso(),
  });
}
