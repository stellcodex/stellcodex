import { Suspense } from "react";
import { PageShell } from "@/components/layout/PageShell";
import Viewer2DClient from "./Viewer2DClient";

export default function Page() {
  return (
    <Suspense
      fallback={
        <PageShell title="2D Viewer" subtitle="PDF ve görsel dosyaları için hızlı görüntüleme.">
          <div className="text-sm text-slate-500">Yükleniyor...</div>
        </PageShell>
      }
    >
      <Viewer2DClient />
    </Suspense>
  );
}
