import { NextResponse } from "next/server";
import { getDefaultProject } from "@/lib/stellcodex/mock-db";

export async function GET() {
  const project = getDefaultProject();
  return NextResponse.json({ projectId: project.id, name: project.name });
}

