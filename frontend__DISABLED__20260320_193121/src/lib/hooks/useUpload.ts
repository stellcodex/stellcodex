"use client";

import * as React from "react";

import { uploadFile } from "@/lib/api/files";
import { useUploadStore } from "@/lib/stores/uploadStore";

export function useUpload() {
  const { clearItem, items, upsertItem } = useUploadStore();
  const [activeFileId, setActiveFileId] = React.useState<string | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  const upload = React.useCallback(async (file: File, projectId?: string) => {
    const localId = `${file.name}-${Date.now()}`;
    setError(null);
    setActiveFileId(null);
    upsertItem({
      localId,
      fileName: file.name,
      progress: 0,
      status: "queued",
    });
    try {
      const result = await uploadFile(file, {
        projectId,
        onProgress: ({ fileId, progress }) => {
          upsertItem({
            localId,
            fileName: file.name,
            progress,
            status: progress >= 100 ? "success" : "uploading",
            fileId,
          });
        },
      });
      setActiveFileId(result.file_id);
      return result.file_id;
    } catch (caughtError) {
      const message = caughtError instanceof Error ? caughtError.message : "Upload failed.";
      setError(message);
      upsertItem({
        localId,
        fileName: file.name,
        progress: 100,
        status: "failed",
        error: message,
      });
      throw caughtError;
    }
  }, [upsertItem]);

  return {
    items,
    upload,
    activeFileId,
    error,
    clearUpload: clearItem,
  };
}
