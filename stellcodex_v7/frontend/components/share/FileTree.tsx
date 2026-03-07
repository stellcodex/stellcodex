"use client";

import type { FolderRecord } from "@/lib/stellcodex/types";
import { clsx } from "clsx";

export function FileTree({
  folders,
  currentFolderId,
  onSelectFolder,
}: {
  folders: FolderRecord[];
  currentFolderId: string | null;
  onSelectFolder: (id: string | null) => void;
}) {
  const roots = folders.filter((f) => !f.parentId);
  const childrenByParent = new Map<string, FolderRecord[]>();
  for (const folder of folders) {
    if (!folder.parentId) continue;
    const list = childrenByParent.get(folder.parentId) || [];
    list.push(folder);
    childrenByParent.set(folder.parentId, list);
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-3">
      <div className="mb-2 px-2 text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
        Klasörler
      </div>
      <button
        className={clsx(
          "mb-1 w-full rounded-lg px-2 py-2 text-left text-sm",
          currentFolderId === null ? "bg-slate-900 text-white" : "hover:bg-slate-100"
        )}
        onClick={() => onSelectFolder(null)}
      >
        Tümü
      </button>
      <div className="grid gap-1">
        {roots.map((folder) => (
          <div key={folder.id}>
            <button
              className={clsx(
                "flex w-full items-center justify-between rounded-lg px-2 py-2 text-left text-sm",
                currentFolderId === folder.id ? "bg-slate-900 text-white" : "hover:bg-slate-100"
              )}
              onClick={() => onSelectFolder(folder.id)}
            >
              <span className="truncate">{folder.name}</span>
              {folder.isSystem ? (
                <span
                  className={clsx(
                    "ml-2 rounded-full px-2 py-0.5 text-[10px] uppercase",
                    currentFolderId === folder.id ? "bg-white/15 text-white" : "bg-slate-100 text-slate-500"
                  )}
                >
                  Sistem
                </span>
              ) : null}
            </button>
            {(childrenByParent.get(folder.id) || []).map((child) => (
              <button
                key={child.id}
                className={clsx(
                  "ml-4 mt-1 flex w-[calc(100%-1rem)] items-center justify-between rounded-lg px-2 py-2 text-left text-sm",
                  currentFolderId === child.id ? "bg-slate-900 text-white" : "hover:bg-slate-100"
                )}
                onClick={() => onSelectFolder(child.id)}
              >
                <span className="truncate">{child.name}</span>
              </button>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

