import { NextResponse } from "next/server";
import { listArchive } from "@/lib/stellcodex/mock-db";

export async function GET(_: Request, { params }: { params: Promise<{ fileId: string }> }) {
  const { fileId } = await params;
  const entries = listArchive(fileId);
  if (!entries) return NextResponse.json({ error: "Arşiv bulunamadı." }, { status: 404 });
  return NextResponse.json({ entries });
}

