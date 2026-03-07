"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/common/Button";
import { ProcessingScreen } from "@/components/upload/ProcessingScreen";
import { getFile, getJob, resolveViewer } from "@/lib/api";
import type { FileDetailResponse, ViewerEngine } from "@/lib/stellcodex/types";
import { useViewerStore } from "@/lib/stellcodex/view-store";
import { ViewerTabs } from "@/components/view/ViewerTabs";
import { ViewerHost } from "@/components/view/ViewerHost";

type LoadingState =
  | { kind: "idle" }
  | { kind: "processing"; stage: "uploaded" | "security" | "preview" | "ready"; progress: number; fileId: string; fileName?: string }
  | { kind: "error"; message: string };

export function ViewWorkspace({ initialFileId }: { initialFileId?: string }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const routeFileId = searchParams.get("file") || initialFileId || undefined;
  const { tabs, activeFileId, openTab, closeTab, setActive } = useViewerStore();
  const [records, setRecords] = useState<Record<string, FileDetailResponse>>({});
  const [engines, setEngines] = useState<Record<string, ViewerEngine>>({});
  const [loading, setLoading] = useState<LoadingState>({ kind: "idle" });

  useEffect(() => {
    if (!routeFileId) return;
    let cancelled = false;
    async function ensureOpen() {
      try {
        const detail = await getFile(routeFileId);
        if (cancelled) return;
        setRecords((prev) => ({ ...prev, [routeFileId]: detail }));
        const job = detail.job;
        if (job && job.stage !== "ready") {
          setLoading({
            kind: "processing",
            stage: job.stage,
            progress: job.progress,
            fileId: routeFileId,
            fileName: detail.file.name,
          });
          for (let i = 0; i < 80; i++) {
            const next = await getJob(job.id);
            if (cancelled) return;
            setLoading({
              kind: "processing",
              stage: next.stage,
              progress: next.progress,
              fileId: routeFileId,
              fileName: detail.file.name,
            });
            if (next.stage === "ready") break;
            await new Promise((r) => setTimeout(r, 700));
          }
        }
        const resolved = await resolveViewer(routeFileId);
        if (cancelled) return;
        setEngines((prev) => ({ ...prev, [routeFileId]: resolved.engine }));
        openTab({
          id: routeFileId,
          fileId: routeFileId,
          label: detail.file.name,
          kind: resolved.kind,
          engine: resolved.engine,
        });
        setLoading({ kind: "idle" });
        router.replace(`/view?file=${routeFileId}`);
      } catch (e) {
        if (!cancelled) {
          setLoading({ kind: "error", message: e instanceof Error ? e.message : "Viewer açılamadı." });
        }
      }
    }
    void ensureOpen();
    return () => {
      cancelled = true;
    };
  }, [routeFileId, openTab, router]);

  const active = useMemo(() => {
    const id = activeFileId || tabs[0]?.fileId || null;
    if (!id) return null;
    const detail = records[id];
    const engine = engines[id] || tabs.find((t) => t.fileId === id)?.engine;
    if (!detail || !engine) return null;
    return { id, detail, engine };
  }, [activeFileId, tabs, records, engines]);

  if (loading.kind === "error") {
    return <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-sm text-red-700">{loading.message}</div>;
  }

  return (
    <div className="grid gap-4">
      <div className="rounded-2xl border border-slate-200 bg-white p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-lg font-semibold text-slate-900">StellView</h1>
            <p className="text-sm text-slate-600">Motor backend/mock tarafından belirlenir. Paylaşım bu ekranda yok.</p>
          </div>
          <Button href="/dashboard">Panel&apos;e dön</Button>
        </div>
      </div>

      {loading.kind === "processing" ? (
        <ProcessingScreen
          stage={loading.stage}
          progress={loading.progress}
          title="Hazırlanıyor"
          subtitle={`${loading.fileName || "Dosya"} işleniyor. Viewer hazır olmadan gösterilmeyecek.`}
        />
      ) : null}

      <div className="rounded-2xl border border-slate-200 bg-white">
        <ViewerTabs
          tabs={tabs}
          activeFileId={active?.id || null}
          onSelect={(fileId) => {
            setActive(fileId);
            router.push(`/view?file=${fileId}`);
          }}
          onClose={(fileId) => closeTab(fileId)}
        />
        <div className="p-4">
          {active ? (
            <ViewerHost
              file={{
                id: active.detail.file.id,
                name: active.detail.file.name,
                kind: active.detail.file.kind,
              }}
              engine={active.engine}
            />
          ) : (
            <div className="grid min-h-[420px] place-items-center rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
              <div>
                <div className="text-sm font-medium text-slate-800">Açık dosya yok</div>
                <div className="mt-1 text-sm text-slate-500">StellShare üzerinden bir dosya açın veya Home ekranından yükleyin.</div>
                <div className="mt-4 flex justify-center gap-2">
                  <Button href="/dashboard">Panel</Button>
                  <Button href="/" variant="primary">
                    Home
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

