"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
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

  useEffect(() => {
    const workspace = ensureSession();
    const targetPath = buildWorkspacePath(workspace.id, suffix);
    const search = preserveSearch && typeof window !== "undefined" ? window.location.search.replace(/^\?/, "") : "";
    const target = search ? `${targetPath}?${search}` : targetPath;

    if (pathname === targetPath) return;
    router.replace(target);
  }, [pathname, preserveSearch, router, suffix]);

  return (
    <div className="auth-shell">
      <section className="hero-card" style={{ maxWidth: "680px" }}>
        <div className="eyebrow">Workspace routing</div>
        <h1 className="page-title">Preparing the active workspace</h1>
        <p className="page-copy">Canonical routes stay inside one shell. Redirecting now.</p>
      </section>
    </div>
  );
}
