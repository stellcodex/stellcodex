"use client";

import { useEffect } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { ensureSession } from "@/lib/sessionStore";
import { buildWorkspacePath } from "@/lib/workspace-routing";

export function WorkspaceRedirect({
  suffix = "",
  preserveSearch = false,
}: {
  suffix?: string;
  preserveSearch?: boolean;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  useEffect(() => {
    const workspace = ensureSession();
    const baseTarget = buildWorkspacePath(workspace.id, suffix);
    const search = preserveSearch ? searchParams.toString() : "";
    const target = search ? `${baseTarget}?${search}` : baseTarget;
    if (pathname === baseTarget) return;
    router.replace(target);
  }, [pathname, preserveSearch, router, searchParams, suffix]);

  return (
    <div className="grid min-h-screen place-items-center bg-[var(--platform-bg)] px-6 text-center text-sm text-slate-500">
      Workspace hazirlaniyor...
    </div>
  );
}
