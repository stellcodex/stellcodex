"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  createShare,
  ExplorerFolder,
  ExplorerItem,
  fetchAuthedBlobUrl,
  getExplorerList,
  getExplorerTree,
  getFile,
  setVisibility,
} from "@/services/api";

type ViewMode = "grid" | "list";

function fmtBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function fmtDate(value: string) {
  const dt = new Date(value);
  if (Number.isNaN(dt.getTime())) return value;
  return dt.toLocaleString("tr-TR", { year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
}

function statusLabel(status: string) {
  const value = (status || "").toLowerCase();
  if (value === "ready" || value === "succeeded") return "Hazır";
  if (value === "queued" || value === "pending") return "Sırada";
  if (value === "running" || value === "processing") return "İşleniyor";
  if (value === "failed") return "Hata";
  return status || "Bilinmiyor";
}

function statusClass(status: string) {
  const value = (status || "").toLowerCase();
  if (value === "ready" || value === "succeeded") return "border-emerald-200 bg-emerald-50 text-emerald-700";
  if (value === "failed") return "border-red-200 bg-red-50 text-red-700";
  if (value === "running" || value === "processing") return "border-amber-200 bg-amber-50 text-amber-700";
  return "border-slate-200 bg-slate-50 text-slate-600";
}

function kindIcon(kind: string) {
  if (kind === "3d") return "3D";
  if (kind === "2d") return "2D";
  if (kind === "doc") return "DOC";
  if (kind === "image") return "IMG";
  return "FILE";
}

function folderDepth(key: string) {
  return Math.max(0, key.split("/").length - 2);
}

export default function FilesPage() {
  const router = useRouter();
  const [folders, setFolders] = useState<ExplorerFolder[]>([]);
  const [items, setItems] = useState<ExplorerItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [folderKey, setFolderKey] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState<"newest" | "oldest">("newest");
  const [filter, setFilter] = useState<string>("");
  const [viewMode, setViewMode] = useState<ViewMode>("grid");
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [anchorIndex, setAnchorIndex] = useState<number | null>(null);
  const [shareLink, setShareLink] = useState<string | null>(null);
  const [previewIndex, setPreviewIndex] = useState(0);

  const selectedMap = useMemo(() => new Set(selectedIds), [selectedIds]);

  const activeItem = useMemo(() => {
    if (!selectedIds.length) return null;
    return items.find((item) => item.file_id === selectedIds[selectedIds.length - 1]) || null;
  }, [items, selectedIds]);

  const previewUrls = activeItem?.preview_urls || (activeItem?.thumb_url ? [activeItem.thumb_url] : []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [tree, list] = await Promise.all([
        getExplorerTree("default"),
        getExplorerList({
          projectId: "default",
          folderKey: folderKey || undefined,
          q: query || undefined,
          sort,
          filter: filter || undefined,
        }),
      ]);
      setFolders(tree.folders);
      setItems(list.items);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Explorer yüklenemedi.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [folderKey, query, sort, filter]);

  useEffect(() => {
    setPreviewIndex(0);
  }, [activeItem?.file_id]);

  const handleSelectItem = (item: ExplorerItem, index: number, event: React.MouseEvent) => {
    const withToggle = event.metaKey || event.ctrlKey;
    const withRange = event.shiftKey;

    if (withRange && anchorIndex !== null) {
      const [start, end] = anchorIndex < index ? [anchorIndex, index] : [index, anchorIndex];
      const ranged = items.slice(start, end + 1).map((row) => row.file_id);
      setSelectedIds((prev) => Array.from(new Set([...prev, ...ranged])));
      return;
    }

    if (withToggle) {
      setSelectedIds((prev) => (prev.includes(item.file_id) ? prev.filter((id) => id !== item.file_id) : [...prev, item.file_id]));
      setAnchorIndex(index);
      return;
    }

    setSelectedIds([item.file_id]);
    setAnchorIndex(index);
  };

  const handleBulkArchive = async () => {
    if (!selectedIds.length) return;
    await Promise.all(selectedIds.map((fileId) => setVisibility(fileId, "hidden")));
    setSelectedIds([]);
    await loadData();
  };

  const handleBulkShare = async () => {
    if (!selectedIds.length) return;
    const first = selectedIds[0];
    const result = await createShare(first);
    setShareLink(`${window.location.origin}/s/${result.token}`);
  };

  const handleDownload = async (item: ExplorerItem | null) => {
    if (!item) return;
    const detail = await getFile(item.file_id);
    const target = detail.original_url || detail.preview_url || detail.gltf_url || detail.preview_urls?.[0];
    if (!target) return;
    const blobUrl = await fetchAuthedBlobUrl(target);
    const a = document.createElement("a");
    a.href = blobUrl;
    a.download = detail.original_filename || `${detail.file_id}.${detail.kind}`;
    a.click();
    URL.revokeObjectURL(blobUrl);
  };

  return (
    <main className="mx-auto max-w-[1600px] px-4 py-5 sm:px-6">
      <header className="mb-4 rounded-2xl border border-[#e7e5e4] bg-white p-4">
        <div className="flex flex-wrap items-center gap-2">
          <div className="text-lg font-semibold text-[#111827]">Dosya Kütüphanesi</div>
          <span className="rounded-full border border-[#d6d3d1] bg-[#fafaf9] px-2 py-0.5 text-xs text-[#57534e]">Windows Explorer görünümü</span>
        </div>
        <div className="mt-3 grid gap-2 md:grid-cols-[1fr_auto_auto_auto]">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ara..."
            className="h-10 rounded-lg border border-[#d6d3d1] bg-white px-3 text-sm"
          />
          <select value={sort} onChange={(e) => setSort(e.target.value as "newest" | "oldest")} className="h-10 rounded-lg border border-[#d6d3d1] bg-white px-3 text-sm">
            <option value="newest">En yeni</option>
            <option value="oldest">En eski</option>
          </select>
          <select value={filter} onChange={(e) => setFilter(e.target.value)} className="h-10 rounded-lg border border-[#d6d3d1] bg-white px-3 text-sm">
            <option value="">Tüm türler</option>
            <option value="brep">3D / B-Rep</option>
            <option value="mesh_approx">3D / Mesh</option>
            <option value="visual_only">3D / Visual</option>
            <option value="2d_only">2D</option>
            <option value="doc">Docs</option>
            <option value="image">Images</option>
          </select>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => setViewMode("grid")}
              className={`h-10 rounded-lg border text-sm ${viewMode === "grid" ? "border-[#111827] bg-[#111827] text-white" : "border-[#d6d3d1] bg-white text-[#44403c]"}`}
            >
              Grid
            </button>
            <button
              type="button"
              onClick={() => setViewMode("list")}
              className={`h-10 rounded-lg border text-sm ${viewMode === "list" ? "border-[#111827] bg-[#111827] text-white" : "border-[#d6d3d1] bg-white text-[#44403c]"}`}
            >
              List
            </button>
          </div>
        </div>
      </header>

      {selectedIds.length > 0 ? (
        <div className="mb-3 flex flex-wrap items-center gap-2 rounded-xl border border-[#d6d3d1] bg-[#fafaf9] px-3 py-2">
          <span className="text-sm text-[#44403c]">{selectedIds.length} dosya seçili</span>
          <button type="button" onClick={handleBulkShare} className="rounded-lg border border-[#111827] bg-[#111827] px-3 py-1.5 text-xs font-semibold text-white">
            Bulk Share
          </button>
          <button type="button" onClick={handleBulkArchive} className="rounded-lg border border-[#d6d3d1] bg-white px-3 py-1.5 text-xs font-semibold text-[#44403c]">
            Bulk Archive
          </button>
          {shareLink ? <span className="truncate text-xs text-[#1d4ed8]">{shareLink}</span> : null}
        </div>
      ) : null}

      <div className="grid gap-3 lg:grid-cols-[250px_minmax(0,1fr)_330px]">
        <aside className="rounded-2xl border border-[#e7e5e4] bg-white p-3">
          <button
            type="button"
            onClick={() => setFolderKey(null)}
            className={`mb-2 w-full rounded-lg border px-2 py-2 text-left text-sm ${folderKey === null ? "border-[#111827] bg-[#111827] text-white" : "border-[#d6d3d1] bg-white text-[#44403c]"}`}
          >
            Tüm Dosyalar
          </button>
          <div className="max-h-[72vh] overflow-auto pr-1">
            {folders.map((folder) => (
              <button
                key={folder.folder_key}
                type="button"
                onClick={() => setFolderKey(folder.folder_key)}
                className={`mt-1 flex w-full items-center justify-between rounded-lg border px-2 py-1.5 text-left text-xs ${
                  folderKey === folder.folder_key ? "border-[#111827] bg-[#111827] text-white" : "border-[#e7e5e4] bg-white text-[#57534e]"
                }`}
                style={{ paddingLeft: `${folderDepth(folder.folder_key) * 10 + 8}px` }}
              >
                <span className="truncate">{folder.label}</span>
                <span>{folder.item_count}</span>
              </button>
            ))}
          </div>
        </aside>

        <section className="rounded-2xl border border-[#e7e5e4] bg-white p-3">
          {loading ? <div className="p-6 text-sm text-[#6b7280]">Yükleniyor...</div> : null}
          {error ? <div className="p-6 text-sm text-red-600">{error}</div> : null}
          {!loading && !error && items.length === 0 ? <div className="p-6 text-sm text-[#6b7280]">Bu klasörde dosya yok.</div> : null}

          {!loading && !error && items.length > 0 && viewMode === "grid" ? (
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              {items.map((item, index) => (
                <button
                  key={item.file_id}
                  type="button"
                  onClick={(event) => handleSelectItem(item, index, event)}
                  onDoubleClick={() => router.push(item.open_url)}
                  className={`rounded-xl border p-3 text-left ${selectedMap.has(item.file_id) ? "border-[#111827] bg-[#f8fafc]" : "border-[#e7e5e4] bg-white"}`}
                >
                  <div className="mb-2 flex items-center justify-between gap-2">
                    <span className="truncate text-sm font-semibold text-[#111827]">{item.name}</span>
                    <span className="text-base">{kindIcon(item.kind)}</span>
                  </div>
                  <div className="grid h-28 place-items-center rounded-lg border border-dashed border-[#d6d3d1] bg-[#fafaf9]">
                    {item.thumb_url ? <img src={item.thumb_url} alt={item.name} className="h-full w-full rounded-lg object-cover" /> : <span className="text-xs text-[#6b7280]">No thumb</span>}
                  </div>
                  <div className="mt-2 flex items-center justify-between text-xs">
                    <span className={`rounded-full border px-2 py-0.5 ${statusClass(item.status)}`}>{statusLabel(item.status)}</span>
                    <span className="text-[#6b7280]">{item.mode}</span>
                  </div>
                </button>
              ))}
            </div>
          ) : null}

          {!loading && !error && items.length > 0 && viewMode === "list" ? (
            <div className="overflow-x-auto">
              <div className="grid grid-cols-[2fr_1fr_120px_150px_120px_140px] gap-2 border-b border-[#e7e5e4] px-2 py-2 text-xs font-semibold text-[#6b7280]">
                <span>Name</span>
                <span>Type</span>
                <span>Size</span>
                <span>Date</span>
                <span>Status</span>
                <span>Mode</span>
              </div>
              {items.map((item, index) => (
                <button
                  key={item.file_id}
                  type="button"
                  onClick={(event) => handleSelectItem(item, index, event)}
                  onDoubleClick={() => router.push(item.open_url)}
                  className={`grid w-full grid-cols-[2fr_1fr_120px_150px_120px_140px] gap-2 border-b border-[#f1f5f9] px-2 py-2 text-left text-xs ${
                    selectedMap.has(item.file_id) ? "bg-[#f8fafc]" : "bg-white hover:bg-[#f8fafc]"
                  }`}
                >
                  <span className="truncate text-[#111827]">{item.name}</span>
                  <span className="text-[#57534e]">{item.kind}</span>
                  <span className="text-[#57534e]">{fmtBytes(item.size)}</span>
                  <span className="text-[#57534e]">{fmtDate(item.created_at)}</span>
                  <span className={`inline-flex w-fit rounded-full border px-2 py-0.5 ${statusClass(item.status)}`}>{statusLabel(item.status)}</span>
                  <span className="text-[#57534e]">{item.mode}</span>
                </button>
              ))}
            </div>
          ) : null}
        </section>

        <aside className="rounded-2xl border border-[#e7e5e4] bg-white p-3">
          {!activeItem ? <div className="text-sm text-[#6b7280]">Inspector için bir dosya seçin.</div> : null}
          {activeItem ? (
            <div className="space-y-3">
              <div>
                <div className="text-sm font-semibold text-[#111827]">{activeItem.name}</div>
                <div className="text-xs text-[#6b7280]">{activeItem.kind} / {activeItem.mode}</div>
              </div>

              <div className="rounded-xl border border-[#d6d3d1] bg-[#fafaf9] p-2">
                <div className="grid h-44 place-items-center overflow-hidden rounded-lg border border-dashed border-[#d6d3d1] bg-white">
                  {previewUrls.length > 0 ? (
                    previewUrls[previewIndex]?.endsWith(".pdf") ? (
                      <iframe src={previewUrls[previewIndex]} className="h-full w-full" />
                    ) : (
                      <img src={previewUrls[previewIndex]} alt={activeItem.name} className="h-full w-full object-cover" />
                    )
                  ) : (
                    <span className="text-xs text-[#6b7280]">Preview yok</span>
                  )}
                </div>
                {previewUrls.length > 1 ? (
                  <div className="mt-2 grid grid-cols-3 gap-2">
                    {previewUrls.map((url, idx) => (
                      <button
                        key={url}
                        type="button"
                        onClick={() => setPreviewIndex(idx)}
                        className={`h-8 rounded border text-xs ${previewIndex === idx ? "border-[#111827] bg-[#111827] text-white" : "border-[#d6d3d1] bg-white text-[#44403c]"}`}
                      >
                        {idx + 1}
                      </button>
                    ))}
                  </div>
                ) : null}
              </div>

              <div className="grid gap-1 rounded-lg border border-[#e7e5e4] bg-[#fafaf9] p-2 text-xs text-[#44403c]">
                <div>X×Y×Z: {`${activeItem.bbox_meta?.x ?? "-"} × ${activeItem.bbox_meta?.y ?? "-"} × ${activeItem.bbox_meta?.z ?? "-"}`} mm</div>
                <div>Part Count: {activeItem.part_count ?? "-"}</div>
                <div>Boyut: {fmtBytes(activeItem.size)}</div>
                <div>Tarih: {fmtDate(activeItem.created_at)}</div>
              </div>

              <div className="grid gap-2">
                <button type="button" onClick={() => router.push(activeItem.open_url)} className="h-9 rounded-lg border border-[#111827] bg-[#111827] text-xs font-semibold text-white">
                  Open Viewer
                </button>
                <button
                  type="button"
                  onClick={async () => {
                    const result = await createShare(activeItem.file_id);
                    setShareLink(`${window.location.origin}/s/${result.token}`);
                  }}
                  className="h-9 rounded-lg border border-[#d6d3d1] bg-white text-xs font-semibold text-[#44403c]"
                >
                  Create Share
                </button>
                <button type="button" onClick={() => void handleDownload(activeItem)} className="h-9 rounded-lg border border-[#d6d3d1] bg-white text-xs font-semibold text-[#44403c]">
                  Download
                </button>
                <button
                  type="button"
                  onClick={async () => {
                    await setVisibility(activeItem.file_id, "hidden");
                    setSelectedIds([]);
                    await loadData();
                  }}
                  className="h-9 rounded-lg border border-[#d6d3d1] bg-white text-xs font-semibold text-[#44403c]"
                >
                  Archive
                </button>
              </div>
              {shareLink ? <div className="rounded-lg border border-[#dbeafe] bg-[#eff6ff] px-2 py-2 text-xs text-[#1d4ed8] break-all">{shareLink}</div> : null}
            </div>
          ) : null}
        </aside>
      </div>
    </main>
  );
}
