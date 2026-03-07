import { NextResponse } from "next/server";
import { resolveViewer } from "@/lib/stellcodex/mock-db";

export async function GET(req: Request) {
  const url = new URL(req.url);
  const fileId = url.searchParams.get("fileId") || "";
  if (!fileId) return NextResponse.json({ error: "fileId gerekli." }, { status: 400 });
  const result = resolveViewer(fileId);
  if (!result) return NextResponse.json({ error: "Dosya bulunamadı." }, { status: 404 });
  return NextResponse.json(result);
}

