import { Suspense } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { ViewWorkspace } from "@/components/view/ViewWorkspace";

export default function ViewPage() {
  return (
    <AppShell>
      <Suspense fallback={<div className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-600">Viewer yükleniyor...</div>}>
        <ViewWorkspace />
      </Suspense>
    </AppShell>
  );
}
