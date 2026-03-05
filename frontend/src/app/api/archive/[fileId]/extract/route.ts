import { NextResponse } from "next/server";
import { apiBase, readErrorMessage, readPayload, upstreamHeaders } from "@/app/api/_lib/upstream";

export async function POST(req: Request, { params }: { params: Promise<{ fileId: string }> }) {
  const { fileId } = await params;
  const upstream = await fetch(`${apiBase()}/files/${encodeURIComponent(fileId)}/archive/manifest`, {
    headers: upstreamHeaders(req),
    cache: "no-store",
  });
  const payload = await readPayload(upstream);
  if (!upstream.ok) {
    return NextResponse.json(
      { error: readErrorMessage(payload, "Arşiv çıkartılamadı.") },
      { status: upstream.status }
    );
  }

  const entryCount =
    payload && typeof payload === "object" && typeof (payload as { entry_count?: unknown }).entry_count === "number"
      ? Number((payload as { entry_count: number }).entry_count)
      : 0;
  return NextResponse.json({
    newFolderId: `archive-${fileId}`,
    status: "virtual_extract",
    entryCount,
    note: "Archive extraction is represented virtually for preview-safe access.",
  });
}
