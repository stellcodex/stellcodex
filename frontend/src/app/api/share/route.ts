import { NextResponse } from "next/server";
import { apiBase, readErrorMessage, readPayload, upstreamHeaders } from "@/app/api/_lib/upstream";

export async function POST(req: Request) {
  const body = (await req.json().catch(() => ({}))) as Record<string, unknown>;
  const fileId = typeof body.fileId === "string" ? body.fileId : "";
  if (!fileId) return NextResponse.json({ error: "fileId gerekli." }, { status: 400 });

  const canView = body.canView !== false;
  if (!canView) {
    return NextResponse.json({ error: "Paylaşım için görüntüleme izni açık olmalıdır." }, { status: 400 });
  }
  const canDownload = body.canDownload === true;
  const permission = canDownload ? "download" : "view";

  let expiresInSeconds = 7 * 24 * 60 * 60;
  if (typeof body.expiresAt === "string" && body.expiresAt.trim()) {
    const target = Date.parse(body.expiresAt);
    if (Number.isFinite(target)) {
      const delta = Math.round((target - Date.now()) / 1000);
      expiresInSeconds = Math.max(60, Math.min(30 * 24 * 60 * 60, delta));
    }
  }

  const upstream = await fetch(`${apiBase()}/files/${encodeURIComponent(fileId)}/share`, {
    method: "POST",
    headers: upstreamHeaders(req, { "Content-Type": "application/json" }),
    body: JSON.stringify({
      permission,
      expires_in_seconds: expiresInSeconds,
    }),
    cache: "no-store",
  });
  const payload = await readPayload(upstream);
  if (!upstream.ok) {
    return NextResponse.json(
      { error: readErrorMessage(payload, "Paylaşım oluşturulamadı.") },
      { status: upstream.status }
    );
  }

  const token =
    payload && typeof payload === "object" && typeof (payload as { token?: unknown }).token === "string"
      ? String((payload as { token: string }).token)
      : "";
  if (!token) {
    return NextResponse.json({ error: "Paylaşım yanıtı geçersiz (token yok)." }, { status: 502 });
  }
  return NextResponse.json({ shareUrl: `/s/${token}`, token });
}
