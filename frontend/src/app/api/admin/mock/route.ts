import { NextResponse } from "next/server";
import { adminSnapshot } from "@/lib/stellcodex/mock-db";

export async function GET() {
  return NextResponse.json(adminSnapshot());
}

