"use client";

import { WorkspaceRedirect } from "@/components/workspace/WorkspaceRedirect";
import { useSearchParams } from "next/navigation";

export default function WorkspaceEntryPage() {
  const searchParams = useSearchParams();
  const nextPath = (searchParams.get("next") || "").trim();
  const safeNext = nextPath.startsWith("/") ? nextPath : "";
  return <WorkspaceRedirect suffix={safeNext} />;
}
