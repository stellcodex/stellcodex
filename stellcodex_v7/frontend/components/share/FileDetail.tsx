"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Breadcrumbs } from "@/components/common/Breadcrumbs";
import { Button } from "@/components/common/Button";
import { ShareDialog } from "@/components/share/ShareDialog";
import { extractArchive, getFile, listArchive } from "@/lib/api";
import type { FileDetailResponse } from "@/lib/stellcodex/types";

export function FileDetail({ fileId }: { fileId: string }) {
  const [detail, setDetail] = useState<FileDetailResponse | null>(null);
  const [archiveEntries, setArchiveEntries] = useState<Array<{ path: string; sizeBytes: number; kind: string }> | null>(null);
  const [shareOpen, setShareOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const next = await getFile(fileId);
        if (alive) setDetail(next);
      } catch (e) {
        if (alive) setError(e instanceof Error ? e.message : "The file could not be loaded.");
      }
    })();
    return () => {
      alive = false;
    };
  }, [fileId]);

  async function handleListArchive() {
    if (!detail) return;
    setBusy(true);
    setError(null);
    try {
      const result = await listArchive(detail.file.id);
      setArchiveEntries(result.entries as Array<{ path: string; sizeBytes: number; kind: string }>);
    } catch (e) {
      setError(e instanceof Error ? e.message : "The archive could not be read.");
    } finally {
      setBusy(false);
    }
  }

  async function handleExtractArchive() {
    if (!detail) return;
    setBusy(true);
    setError(null);
    try {
      await extractArchive(detail.file.id);
      const refreshed = await getFile(detail.file.id);
      setDetail(refreshed);
      await handleListArchive();
    } catch (e) {
      setError(e instanceof Error ? e.message : "The archive could not be extracted.");
    } finally {
      setBusy(false);
    }
  }

  if (error && !detail) {
    return <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>;
  }
  if (!detail) {
    return <div className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-600">Loading...</div>;
  }

  const { file, inFolder } = detail;

  return (
    <div className="space-y-4">
      <div className="rounded-2xl border border-slate-200 bg-white p-4">
        <Breadcrumbs
          items={[
            { label: "StellShare", href: "/share" },
            ...(inFolder ? [{ label: inFolder.name, href: "/share" }] : []),
            { label: file.name },
          ]}
        />
        <h1 className="mt-3 text-xl font-semibold text-slate-900">{file.name}</h1>
        <p className="mt-1 text-sm text-slate-600">
          {file.kind} · {file.engine} · {Math.round(file.sizeBytes / 1024)} KB
        </p>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-4">
        <div className="mb-3 text-sm font-medium text-slate-700">Preview</div>
        <div className="grid min-h-[340px] place-items-center rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-6 text-center">
          <div>
            <div className="text-sm font-medium text-slate-800">{file.name}</div>
            <div className="mt-1 text-sm text-slate-500">
              {file.kind === "zip" ? "Archive inspection and extraction are handled on this page." : "Preview placeholder"}
            </div>
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-4">
        <div className="flex flex-wrap gap-2">
          <Button href={`/view/file/${file.id}`} variant="primary">
            Open in Viewer
          </Button>
          <Button onClick={() => setShareOpen(true)}>Share</Button>
          <Button href={detail.downloadUrl}>Download</Button>
        </div>

        {file.kind === "zip" ? (
          <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-3">
            <div className="mb-2 text-sm font-medium text-slate-800">
              ZIP archives are not extracted automatically. They remain inside the archive folder.
            </div>
            <div className="flex flex-wrap gap-2">
              <Button onClick={handleListArchive} disabled={busy}>
                View Contents
              </Button>
              <Button onClick={handleExtractArchive} disabled={busy}>
                Extract
              </Button>
              {detail.file.extractedFolderId ? (
                <Link className="self-center text-sm text-slate-600 hover:text-slate-900" href="/dashboard/files">
                  Open the extracted folder in My Files
                </Link>
              ) : null}
            </div>
            {archiveEntries ? (
              <ul className="mt-3 grid gap-1 text-sm text-slate-700">
                {archiveEntries.map((entry) => (
                  <li key={entry.path} className="rounded-lg bg-white px-3 py-2">
                    {entry.path} <span className="text-slate-400">({entry.kind})</span>
                  </li>
                ))}
              </ul>
            ) : null}
          </div>
        ) : null}
        {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}
      </div>

      <ShareDialog open={shareOpen} fileId={file.id} onClose={() => setShareOpen(false)} />
    </div>
  );
}
