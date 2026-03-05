import { NextResponse } from "next/server";
import { apiBase, readErrorMessage, readPayload, upstreamHeaders } from "@/app/api/_lib/upstream";

const MAX_SIZE = 500 * 1024 * 1024;

export async function POST(req: Request) {
  const form = await req.formData();
  const file = form.get("file");
  const projectId = String(form.get("projectId") || "").trim() || undefined;
  if (!(file instanceof File)) {
    return NextResponse.json({ error: "Dosya bulunamadı." }, { status: 400 });
  }
  if (file.size > MAX_SIZE) {
    return NextResponse.json({ error: "Dosya boyutu limiti aşıldı (500MB)." }, { status: 400 });
  }

  const upstreamForm = new FormData();
  upstreamForm.set("upload", file);
  if (projectId) upstreamForm.set("projectId", projectId);

  const upstream = await fetch(`${apiBase()}/files/upload`, {
    method: "POST",
    headers: upstreamHeaders(req),
    body: upstreamForm,
    cache: "no-store",
  });
  const payload = await readPayload(upstream);
  if (!upstream.ok) {
    return NextResponse.json(
      { error: readErrorMessage(payload, "Yükleme başarısız.") },
      { status: upstream.status }
    );
  }

  const fileId =
    payload && typeof payload === "object" && typeof (payload as { file_id?: unknown }).file_id === "string"
      ? String((payload as { file_id: string }).file_id)
      : "";
  if (!fileId) {
    return NextResponse.json({ error: "Yükleme yanıtı geçersiz (file_id yok)." }, { status: 502 });
  }

  return NextResponse.json({ fileId, jobId: `file:${fileId}` });
}
