import { Suspense } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { ViewWorkspace } from "@/components/view/ViewWorkspace";

export default async function ViewFilePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <AppShell>
      <Suspense fallback={<div className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-600">Viewer yükleniyor...</div>}>
        <ViewWorkspace initialFileId={id} />
      </Suspense>
    </AppShell>
  );
}
