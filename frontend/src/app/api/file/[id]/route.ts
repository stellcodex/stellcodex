import { NextResponse } from "next/server";
import { getFileDetail } from "@/lib/stellcodex/mock-db";

function textBody(name: string) {
  return `STELLCODEX placeholder download\nfile=${name}\n`;
}

export async function GET(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const detail = getFileDetail(id);
  if (!detail) return NextResponse.json({ error: "The file could not be found." }, { status: 404 });
  const url = new URL(req.url);
  if (url.searchParams.get("download") === "1") {
    return new Response(textBody(detail.file.name), {
      status: 200,
      headers: {
        "Content-Type": "application/octet-stream",
        "Content-Disposition": `attachment; filename="${detail.file.name}.txt"`,
      },
    });
  }
  return NextResponse.json(detail);
}
