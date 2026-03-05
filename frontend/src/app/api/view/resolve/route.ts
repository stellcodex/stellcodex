import { NextResponse } from "next/server";
import {
  apiBase,
  mapLegacyEngine,
  mapLegacyKind,
  readErrorMessage,
  readPayload,
  upstreamHeaders,
} from "@/app/api/_lib/upstream";

export async function GET(req: Request) {
  const url = new URL(req.url);
  const fileId = url.searchParams.get("fileId") || "";
  if (!fileId) return NextResponse.json({ error: "fileId gerekli." }, { status: 400 });

  const upstream = await fetch(`${apiBase()}/files/${encodeURIComponent(fileId)}`, {
    headers: upstreamHeaders(req),
    cache: "no-store",
  });
  const payload = await readPayload(upstream);
  if (!upstream.ok) {
    return NextResponse.json(
      { error: readErrorMessage(payload, "Dosya bulunamadı.") },
      { status: upstream.status }
    );
  }

  const data = payload && typeof payload === "object" ? (payload as Record<string, unknown>) : {};
  const originalName = typeof data.original_name === "string" ? data.original_name : "";
  const contentType = typeof data.content_type === "string" ? data.content_type : "";
  const kind = mapLegacyKind(data.kind, contentType, originalName);
  const engine = mapLegacyEngine(data.kind, contentType, originalName);

  return NextResponse.json({ engine, kind });
}
