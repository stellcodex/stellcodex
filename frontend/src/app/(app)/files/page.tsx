"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { PageShell } from "@/components/layout/PageShell";
import { UploadDrop } from "@/components/upload/UploadDrop";
import { listFiles, FileItem } from "@/services/api";

const statusLabel: Record<string, string> = {
  pending: "Yükleme bekliyor",
  queued: "Kuyrukta",
  processing: "İşleniyor",
  ready: "Hazır",
  failed: "Başarısız",
};

export default function Page() {
  const [items, setItems] = useState<FileItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  const refresh = async () => {
    try {
      const data = await listFiles();
      setItems(data);
    } catch (e: any) {
      setError(e?.message || "Dosyalar yüklenemedi.");
    }
  };

  useEffect(() => {
    void refresh();
    const id = setInterval(() => void refresh(), 6000);
    return () => clearInterval(id);
  }, []);

  return (
    <PageShell title="Yüklemeler" subtitle="Dosya yükle, durumunu takip et ve görüntüle.">
      <div className="grid gap-6 lg:grid-cols-[360px_1fr]">
        <UploadDrop onUploaded={() => void refresh()} />

        <div className="rounded-3xl border border-slate-200 bg-white p-4">
          <div className="text-sm font-semibold text-slate-900">Dosya Listesi</div>
          <div className="mt-4 grid gap-3">
            {error ? <div className="text-sm text-red-600">{error}</div> : null}

            {items.length === 0 ? (
              <div className="text-sm text-slate-500">Henüz dosya yüklenmedi.</div>
            ) : null}

            {items.map((f) => (
              <div
                key={f.file_id}
                className="flex items-center justify-between rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3"
              >
                <div>
                  <div className="text-sm font-semibold text-slate-900">{f.original_filename}</div>
                  <div className="text-xs text-slate-500">
                    {statusLabel[f.status] || f.status}
                  </div>
                  {f.status === "failed" && f.error ? (
                    <div className="text-xs text-red-600">{f.error}</div>
                  ) : null}
                </div>
                <div className="flex items-center gap-2 text-xs">
                  {f.status === "ready" ? (
                    <Link
                      className="rounded-lg border border-slate-200 bg-white px-3 py-1 text-slate-700"
                      href={`/view/${f.file_id}`}
                    >
                      Görüntüle
                    </Link>
                  ) : null}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </PageShell>
  );
}
