"use client";

import { useEffect, useState } from "react";
import { LayoutShell } from "@/components/layout/LayoutShell";
import { ListRow } from "@/components/common/ListRow";
import { FileItem, listFiles } from "@/services/api";

function toStatusLabel(status: string) {
  const value = (status || "").toLowerCase();
  if (value === "ready" || value === "succeeded") return "Hazır";
  if (value === "queued" || value === "pending") return "Sırada";
  if (value === "running" || value === "processing") return "İşleniyor";
  if (value === "failed") return "Hata";
  return status || "Bilinmiyor";
}

function toAppHref(item: FileItem) {
  const lower = item.original_filename.toLowerCase();
  if (lower.endsWith(".dxf") || item.content_type === "application/pdf" || item.content_type.startsWith("image/")) {
    return `/apps/2d?scx=${item.file_id}`;
  }
  return `/apps/3d?scx=${item.file_id}`;
}

export default function FilesPage() {
  const [items, setItems] = useState<FileItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    void listFiles()
      .then((data) => {
        if (!active) return;
        setItems(data);
      })
      .catch((err: unknown) => {
        if (!active) return;
        setError(err instanceof Error ? err.message : "Dosyalar yüklenemedi.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  return (
    <LayoutShell>
      <div className="flex flex-col gap-sectionGap">
        <div className="text-fs2 font-semibold">Dosyalar</div>
        {loading ? <div className="text-fs0 text-muted">Yükleniyor...</div> : null}
        {error ? <div className="text-fs0 text-red-600">{error}</div> : null}
        {!loading && !error && items.length === 0 ? (
          <div className="text-fs0 text-muted">Henüz dosya yok.</div>
        ) : null}
        {!loading && !error && items.length > 0 ? (
          <div className="flex flex-col gap-cardGap">
            {items.map((file) => (
              <ListRow
                key={file.file_id}
                title={file.original_filename}
                subtitle={toStatusLabel(file.status)}
                href={`/view/${file.file_id}`}
                trailing={toAppHref(file).includes("/apps/2d") ? "2D" : "3D"}
              />
            ))}
          </div>
        ) : null}
      </div>
    </LayoutShell>
  );
}
