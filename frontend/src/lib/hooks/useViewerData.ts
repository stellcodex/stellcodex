"use client";

import * as React from "react";

import { getFile, getFileManifest, getFileStatus } from "@/lib/api/files";
import { mapViewerModel } from "@/lib/mappers/fileMappers";

export function useViewerData(fileId: string) {
  const [viewer, setViewer] = React.useState<ReturnType<typeof mapViewerModel> | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  const refresh = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [file, status] = await Promise.all([getFile(fileId), getFileStatus(fileId)]);
      const manifest = file.kind === "3d" ? await getFileManifest(fileId).catch(() => null) : null;
      setViewer(mapViewerModel({ file, status, manifest }));
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Viewer data could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, [fileId]);

  React.useEffect(() => {
    void refresh();
  }, [refresh]);

  return { viewer, loading, error, refresh };
}
