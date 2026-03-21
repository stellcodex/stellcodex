import { NextResponse } from "next/server";
import { resolveViewer } from "@/lib/stellcodex/mock-db";

export async function GET(req: Request) {
  const url = new URL(req.url);
  const fileId = url.searchParams.get("fileId") || "";
  if (!fileId) return NextResponse.json({ error: "fileId is required." }, { status: 400 });
  const result = resolveViewer(fileId);
  if (!result) return NextResponse.json({ error: "The file could not be found." }, { status: 404 });
  return NextResponse.json(result);
}
