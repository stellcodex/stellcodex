import { NextResponse } from "next/server";
import { getShareByToken } from "@/lib/stellcodex/mock-db";

export async function GET(_: Request, { params }: { params: Promise<{ token: string }> }) {
  const { token } = await params;
  const result = getShareByToken(token);
  if (!result) return NextResponse.json({ error: "The share link could not be found." }, { status: 404 });
  return NextResponse.json({
    file: result.file,
    previewUrl: result.previewUrl,
    downloadUrl: result.downloadUrl,
    canView: result.share.canView,
    canDownload: result.share.canDownload,
    expiresAt: result.share.expiresAt,
  });
}
