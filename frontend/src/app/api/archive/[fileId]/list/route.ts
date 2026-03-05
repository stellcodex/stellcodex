import { NextResponse } from "next/server";
import { apiBase, extOf, mapLegacyKind, readErrorMessage, readPayload, upstreamHeaders } from "@/app/api/_lib/upstream";

function entryKind(entry: Record<string, unknown>) {
  const path = typeof entry.path === "string" ? entry.path : "";
  const ext = extOf(path);
  return mapLegacyKind(ext === "pdf" ? "doc" : undefined, undefined, path);
}

export async function GET(req: Request, { params }: { params: Promise<{ fileId: string }> }) {
  const { fileId } = await params;
  const upstream = await fetch(`${apiBase()}/files/${encodeURIComponent(fileId)}/archive/manifest`, {
    headers: upstreamHeaders(req),
    cache: "no-store",
  });
  const payload = await readPayload(upstream);
  if (!upstream.ok) {
    return NextResponse.json(
      { error: readErrorMessage(payload, "Arşiv bulunamadı.") },
      { status: upstream.status }
    );
  }

  const rawEntries =
    payload && typeof payload === "object" && Array.isArray((payload as { entries?: unknown }).entries)
      ? ((payload as { entries: unknown[] }).entries || [])
      : [];
  const entries = rawEntries
    .filter((entry): entry is Record<string, unknown> => !!entry && typeof entry === "object")
    .map((entry) => ({
      path: typeof entry.path === "string" ? entry.path : "",
      sizeBytes: typeof entry.size_bytes === "number" ? Math.max(0, Math.round(entry.size_bytes)) : 0,
      kind: entryKind(entry),
    }));

  return NextResponse.json({ entries, manifest: payload });
}
