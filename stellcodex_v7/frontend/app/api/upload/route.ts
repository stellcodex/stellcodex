import { NextResponse } from "next/server";
import { createUpload } from "@/lib/stellcodex/mock-db";

const ALLOWED_EXT = new Set([
  "step",
  "stp",
  "iges",
  "igs",
  "stl",
  "obj",
  "sldprt",
  "dxf",
  "pdf",
  "jpg",
  "jpeg",
  "png",
  "webp",
  "docx",
  "xlsx",
  "pptx",
  "zip",
]);
const MAX_SIZE = 200 * 1024 * 1024;

export async function POST(req: Request) {
  const form = await req.formData();
  const file = form.get("file");
  const projectId = String(form.get("projectId") || "").trim() || undefined;
  if (!(file instanceof File)) {
    return NextResponse.json({ error: "Dosya bulunamadı." }, { status: 400 });
  }
  if (file.size > MAX_SIZE) {
    return NextResponse.json({ error: "Dosya boyutu limiti aşıldı (200MB)." }, { status: 400 });
  }
  const ext = (file.name.split(".").pop() || "").toLowerCase();
  if (!ALLOWED_EXT.has(ext)) {
    return NextResponse.json({ error: "Desteklenmeyen dosya uzantısı." }, { status: 400 });
  }
  const result = createUpload({
    projectId,
    fileName: file.name,
    sizeBytes: file.size,
    mime: file.type || null,
  });
  return NextResponse.json(result);
}

