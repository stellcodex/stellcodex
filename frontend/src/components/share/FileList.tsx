"use client";

import type { FileRecord, FolderRecord } from "@/lib/stellcodex/types";
import { clsx } from "clsx";

function fmtBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function FileList({
  folders,
  files,
  selectedFileIds,
  onToggleFile,
  onOpenFile,
  onOpenFolder,
}: {
  folders: FolderRecord[];
  files: FileRecord[];
  selectedFileIds: string[];
  onToggleFile: (id: string) => void;
  onOpenFile: (id: string) => void;
  onOpenFolder: (id: string) => void;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white">
      <div className="grid grid-cols-[1fr_auto_auto] gap-2 border-b border-slate-100 px-4 py-3 text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
        <span>Ad</span>
        <span>Type</span>
        <span>Size</span>
      </div>
      <div className="divide-y divide-slate-100">
        {folders.map((folder) => (
          <button
            key={folder.id}
            onClick={() => onOpenFolder(folder.id)}
            className="grid w-full grid-cols-[1fr_auto_auto] items-center gap-2 px-4 py-3 text-left hover:bg-slate-50"
          >
            <div className="flex min-w-0 items-center gap-2">
              <span className="text-base">📁</span>
              <span className="truncate text-sm text-slate-900">{folder.name}</span>
              {folder.isSystem ? (
                <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] uppercase text-slate-500">
                  System
                </span>
              ) : null}
            </div>
            <span className="text-xs text-slate-500">Folder</span>
            <span className="text-xs text-slate-400">-</span>
          </button>
        ))}
        {files.map((file) => {
          const selected = selectedFileIds.includes(file.id);
          return (
            <div
              key={file.id}
              className={clsx(
                "grid grid-cols-[1fr_auto_auto] items-center gap-2 px-4 py-3",
                selected ? "bg-slate-50" : ""
              )}
            >
              <div className="flex min-w-0 items-center gap-2">
                <input
                  type="checkbox"
                  checked={selected}
                  onChange={() => onToggleFile(file.id)}
                  aria-label={`Select ${file.name}`}
                />
                <button
                  className="min-w-0 flex-1 truncate text-left text-sm text-slate-900 hover:underline"
                  onClick={() => onOpenFile(file.id)}
                  title={file.name}
                >
                  {file.name}
                </button>
              </div>
              <span className="text-xs text-slate-500">{file.kind}</span>
              <span className="text-xs text-slate-500">{fmtBytes(file.sizeBytes)}</span>
            </div>
          );
        })}
        {folders.length === 0 && files.length === 0 ? (
          <div className="px-4 py-10 text-center text-sm text-slate-500">This folder is empty.</div>
        ) : null}
      </div>
    </div>
  );
}
