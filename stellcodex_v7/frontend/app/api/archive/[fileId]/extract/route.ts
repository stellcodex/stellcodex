import { NextResponse } from "next/server";
import { extractArchive } from "@/lib/stellcodex/mock-db";

export async function POST(_: Request, { params }: { params: Promise<{ fileId: string }> }) {
  const { fileId } = await params;
  const result = extractArchive(fileId);
  if (!result) return NextResponse.json({ error: "The archive could not be extracted." }, { status: 404 });
  return NextResponse.json(result);
}
