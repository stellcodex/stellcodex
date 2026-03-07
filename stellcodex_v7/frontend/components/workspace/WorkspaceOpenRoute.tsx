"use client";

import { useEffect, useState } from "react";
import { PlatformClient } from "@/components/platform/PlatformClient";
import { classifyWorkspaceApp } from "@/lib/workspace-routing";
import { getFile } from "@/services/api";

type ViewerAppId = "viewer3d" | "viewer2d" | "docviewer";

export function WorkspaceOpenRoute({ fileId }: { fileId: string }) {
  const [appId, setAppId] = useState<ViewerAppId | null>(null);

  useEffect(() => {
    let active = true;

    (async () => {
      try {
        const file = await getFile(fileId);
        if (!active) return;
        setAppId(classifyWorkspaceApp(file));
      } catch {
        if (!active) return;
        setAppId("viewer3d");
      }
    })();

    return () => {
      active = false;
    };
  }, [fileId]);

  if (!appId) {
    return (
      <div className="grid min-h-screen place-items-center bg-[var(--platform-bg)] px-6 text-center text-sm text-slate-400">
        Dosya rotasi hazirlaniyor...
      </div>
    );
  }

  return <PlatformClient view="app" appId={appId} fileId={fileId} />;
}
