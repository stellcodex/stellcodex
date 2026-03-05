"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Breadcrumbs } from "@/components/common/Breadcrumbs";
import { Button } from "@/components/common/Button";
import { FileList } from "@/components/share/FileList";
import { FileTree } from "@/components/share/FileTree";
import { deleteFiles, getDefaultProject, getProjectTree } from "@/lib/api";
import type { FileRecord, FolderRecord, ProjectTreeResponse } from "@/lib/stellcodex/types";

export function ShareWorkspace() {
  const router = useRouter();
  const [tree, setTree] = useState<ProjectTreeResponse | null>(null);
  const [projectId, setProjectId] = useState<string | null>(null);
  const [currentFolderId, setCurrentFolderId] = useState<string | null>(null);
  const [selectedFileIds, setSelectedFileIds] = useState<string[]>([]);
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const reload = async (pId?: string) => {
    const id = pId || projectId;
    if (!id) return;
    const next = await getProjectTree(id);
    setTree(next);
  };

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        setLoading(true);
        const project = await getDefaultProject();
        if (!alive) return;
        setProjectId(project.projectId);
        const next = await getProjectTree(project.projectId);
        if (!alive) return;
        setTree(next);
      } catch (e) {
        if (alive) setError(e instanceof Error ? e.message : "StellShare yüklenemedi.");
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  const visible = useMemo(() => {
    if (!tree) return { folders: [] as FolderRecord[], files: [] as FileRecord[] };
    const q = query.trim().toLowerCase();
    const folders = tree.folders.filter((f) => (currentFolderId ? f.parentId === currentFolderId : !f.parentId));
    let files = tree.files.filter((f) => (currentFolderId ? f.folderId === currentFolderId : true));
    if (q) {
      files = files.filter((f) => f.name.toLowerCase().includes(q));
    }
    return { folders, files };
  }, [tree, currentFolderId, query]);

  const currentFolder = tree?.folders.find((f) => f.id === currentFolderId) || null;

  async function handleDeleteSelected() {
    if (!projectId || selectedFileIds.length === 0) return;
    if (!window.confirm("Seçili dosyalar silinsin mi?")) return;
    setError(null);
    try {
      await deleteFiles({ projectId, fileIds: selectedFileIds });
      setSelectedFileIds([]);
      await reload(projectId);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Silme işlemi başarısız.");
    }
  }

  if (loading) {
    return <div className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-600">Yükleniyor...</div>;
  }
  if (!tree) {
    return <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-sm text-red-700">{error || "Proje bulunamadı."}</div>;
  }

  return (
    <div className="grid gap-4">
      <div className="rounded-2xl border border-slate-200 bg-white p-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <Breadcrumbs
              items={[
                { label: "StellShare", href: "/share" },
                { label: tree.projectName },
                ...(currentFolder ? [{ label: currentFolder.name }] : []),
              ]}
            />
            <div className="mt-2 text-sm text-slate-600">Varsayılan proje: {tree.projectName}</div>
          </div>
          <div className="flex items-center gap-2">
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="h-10 w-64 rounded-xl border border-slate-200 px-3 text-sm"
              placeholder="Ara"
            />
          </div>
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-[280px_minmax(0,1fr)]">
        <FileTree
          folders={tree.folders}
          currentFolderId={currentFolderId}
          onSelectFolder={(id) => {
            setCurrentFolderId(id);
            setSelectedFileIds([]);
          }}
        />
        <div className="grid gap-3">
          {selectedFileIds.length > 0 ? (
            <div className="flex flex-wrap items-center gap-2 rounded-2xl border border-slate-200 bg-white p-3">
              <span className="text-sm text-slate-600">{selectedFileIds.length} dosya seçili</span>
              <Button onClick={handleDeleteSelected} variant="danger">
                Sil
              </Button>
              {selectedFileIds.length === 1 ? (
                <Button href={`/api/file/${selectedFileIds[0]}?download=1`}>İndir</Button>
              ) : null}
            </div>
          ) : null}
          <FileList
            folders={visible.folders}
            files={visible.files}
            selectedFileIds={selectedFileIds}
            onToggleFile={(id) =>
              setSelectedFileIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))
            }
            onOpenFile={(id) => router.push(`/share/file/${id}`)}
            onOpenFolder={(id) => {
              setCurrentFolderId(id);
              setSelectedFileIds([]);
            }}
          />
          {error ? <p className="text-sm text-red-600">{error}</p> : null}
        </div>
      </div>
    </div>
  );
}
