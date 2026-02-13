"use client";

import { useEffect, useState } from "react";
import { SectionHeader } from "@/components/layout/SectionHeader";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/StateBlocks";
import { FileItem, listFiles } from "@/services/api";

function formatBytes(bytes: number) {
  if (!Number.isFinite(bytes)) return "-";
  if (bytes < 1024) return `${bytes} B`;
  const units = ["KB", "MB", "GB"];
  let val = bytes / 1024;
  let idx = 0;
  while (val >= 1024 && idx < units.length - 1) {
    val /= 1024;
    idx += 1;
  }
  return `${val.toFixed(1)} ${units[idx]}`;
}

export default function DashboardFilesPage() {
  const [items, setItems] = useState<FileItem[]>([]);
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    listFiles()
      .then((data) => {
        if (!mounted) return;
        setItems(data);
        setState("ready");
      })
      .catch((err) => {
        if (!mounted) return;
        setError(err?.message || "Dosyalar yüklenemedi.");
        setState("error");
      });
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Dosya Kütüphanem"
        description="Dosyaları ara, filtrele ve yönet."
        crumbs={[
          { label: "Panel", href: "/dashboard" },
          { label: "Kütüphane" },
        ]}
      />

      <div className="rounded-2xl border border-slate-200 bg-white p-5">
        <div className="flex flex-wrap items-center gap-3">
          <input
            className="flex-1 rounded-xl border border-slate-200 px-3 py-2 text-sm"
            placeholder="Ara"
            disabled
          />
          <select className="rounded-xl border border-slate-200 px-3 py-2 text-sm" disabled>
            <option>Format</option>
          </select>
          <select className="rounded-xl border border-slate-200 px-3 py-2 text-sm" disabled>
            <option>Durum</option>
          </select>
          <select className="rounded-xl border border-slate-200 px-3 py-2 text-sm" disabled>
            <option>Tarih</option>
          </select>
        </div>
        <p className="mt-2 text-xs text-slate-500">
          Filtreler yer tutucudur. Gerçek uç noktalara bağlayın.
        </p>

        <div className="mt-5">
          {state === "loading" ? <LoadingState lines={6} /> : null}
          {state === "error" ? (
            <ErrorState title="Yüklenemedi" description={error || ""} />
          ) : null}
          {state === "ready" && items.length === 0 ? (
            <EmptyState title="Henüz dosya yok" description="Burada görmek için dosya yükleyin." />
          ) : null}
          {state === "ready" && items.length > 0 ? (
            <div className="grid gap-3">
              {items.map((item) => (
                <div
                  key={item.file_id}
                  className="flex flex-col gap-2 rounded-xl border border-slate-100 bg-slate-50 px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div>
                    <div className="text-sm font-semibold text-slate-900">
                      {item.original_filename}
                    </div>
                    <div className="text-xs text-slate-500">
                      {item.status} · {formatBytes(item.size_bytes)}
                    </div>
                  </div>
                  <div className="text-xs text-slate-500">{item.content_type}</div>
                </div>
              ))}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
