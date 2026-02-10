import { Suspense } from "react";
import { PageShell } from "@/components/layout/PageShell";
import Viewer3DClient from "./Viewer3DClient";

export default function Page() {
  return (
    <Suspense
      fallback={
        <PageShell title="3D Viewer" subtitle="Orbit / Pan / Zoom, kesit ve tel kafes.">
          <div className="text-sm text-slate-500">Yükleniyor...</div>
        </PageShell>
      }
    >
      <Viewer3DClient />
    </Suspense>
  );
}
