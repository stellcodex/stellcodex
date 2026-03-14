"use client";

import { useCallback, useState } from "react";
import { uploadFile } from "@/lib/api/files";

export type UploadProgressItem = {
  localId: string;
  fileName: string;
  bytesUploaded: number;
  totalBytes: number;
  status: "pending" | "uploading" | "success" | "failed" | "cancelled";
  error?: string | null;
  fileId?: string;
};

export function useUpload() {
  const [items, setItems] = useState<UploadProgressItem[]>([]);

  const startUpload = useCallback(async (file: File) => {
    const localId = `upload_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    const controller = new AbortController();
    setItems((current) => [
      {
        localId,
        fileName: file.name,
        bytesUploaded: 0,
        totalBytes: file.size,
        status: "pending",
      },
      ...current,
    ]);

    try {
      const result = await uploadFile(file, {
        signal: controller.signal,
        onProgress: (loaded, total) => {
          setItems((current) =>
            current.map((item) =>
              item.localId === localId
                ? { ...item, bytesUploaded: loaded, totalBytes: total, status: "uploading" }
                : item
            )
          );
        },
      });
      setItems((current) =>
        current.map((item) =>
          item.localId === localId ? { ...item, status: "success", fileId: result.file_id } : item
        )
      );
      return result.file_id;
    } catch (error) {
      setItems((current) =>
        current.map((item) =>
          item.localId === localId
            ? {
                ...item,
                status: "failed",
                error: error instanceof Error ? error.message : "Upload failed.",
              }
            : item
        )
      );
      return null;
    }
  }, []);

  return { items, startUpload };
}
