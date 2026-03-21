import { NextResponse } from "next/server";
import { createShare } from "@/lib/stellcodex/mock-db";

export async function POST(req: Request) {
  const body = (await req.json().catch(() => ({}))) as Record<string, unknown>;
  const fileId = typeof body.fileId === "string" ? body.fileId : "";
  if (!fileId) return NextResponse.json({ error: "fileId is required." }, { status: 400 });
  const result = createShare({
    fileId,
    canView: body.canView !== false,
    canDownload: body.canDownload === true,
    password: typeof body.password === "string" ? body.password : null,
    expiresAt: typeof body.expiresAt === "string" ? body.expiresAt : null,
  });
  if (!result) return NextResponse.json({ error: "The file could not be found." }, { status: 404 });
  return NextResponse.json({ shareUrl: result.shareUrl, token: result.share.token });
}
