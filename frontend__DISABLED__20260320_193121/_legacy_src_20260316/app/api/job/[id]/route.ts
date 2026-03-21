import { NextResponse } from "next/server";
import { getJob } from "@/lib/stellcodex/mock-db";

export async function GET(_: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const job = getJob(id);
  if (!job) return NextResponse.json({ error: "The job could not be found." }, { status: 404 });
  return NextResponse.json(job);
}
