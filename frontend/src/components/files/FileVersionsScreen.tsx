"use client";

import * as React from "react";
import Link from "next/link";

import { Button } from "@/components/primitives/Button";
import { ErrorState } from "@/components/primitives/ErrorState";
import { PageHeader } from "@/components/shell/PageHeader";
import { RouteErrorState } from "@/components/states/RouteErrorState";
import { RouteLoadingState } from "@/components/states/RouteLoadingState";
import { getFile, listFileVersions, uploadFileVersion } from "@/lib/api/files";
import { mapFileRecord, mapFileVersionRecord } from "@/lib/mappers/fileMappers";

import { VersionsTable } from "./VersionsTable";

export interface FileVersionsScreenProps {
  fileId: string;
}

export function FileVersionsScreen({ fileId }: FileVersionsScreenProps) {
  const inputRef = React.useRef<HTMLInputElement | null>(null);
  const [file, setFile] = React.useState<ReturnType<typeof mapFileRecord> | null>(null);
  const [versions, setVersions] = React.useState<ReturnType<typeof mapFileVersionRecord>[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [uploading, setUploading] = React.useState(false);
  const [uploadError, setUploadError] = React.useState<string | null>(null);

  const refresh = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [fileResponse, versionResponse] = await Promise.all([getFile(fileId), listFileVersions(fileId)]);
      setFile(mapFileRecord(fileResponse));
      setVersions(versionResponse.map(mapFileVersionRecord));
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "The version history could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, [fileId]);

  React.useEffect(() => {
    void refresh();
  }, [refresh]);

  async function handleUpload(fileToUpload: File | null | undefined) {
    if (!fileToUpload) return;
    setUploadError(null);
    setUploading(true);
    try {
      await uploadFileVersion(fileId, fileToUpload);
      await refresh();
    } catch (caughtError) {
      setUploadError(caughtError instanceof Error ? caughtError.message : "The new version upload failed.");
    } finally {
      setUploading(false);
    }
  }

  if (loading) return <RouteLoadingState title="Loading versions" />;
  if (error || !file) {
    return (
      <RouteErrorState
        actionLabel="Retry"
        description={error || "The file version history could not be loaded."}
        onAction={() => void refresh()}
        title="Versions unavailable"
      />
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        actions={
          <div className="flex flex-wrap gap-3">
            <Link href={`/files/${encodeURIComponent(file.fileId)}`}>
              <Button variant="secondary">Back to file</Button>
            </Link>
            <Button onClick={() => inputRef.current?.click()} variant="primary">
              {uploading ? "Uploading version..." : "Upload new version"}
            </Button>
            <input
              className="hidden"
              onChange={(event) => {
                void handleUpload(event.target.files?.[0]);
                event.currentTarget.value = "";
              }}
              ref={inputRef}
              type="file"
            />
          </div>
        }
        subtitle="Version history and replacement uploads are backed by the live backend file contract."
        title={`Versions · ${file.originalName}`}
      />

      {uploadError ? (
        <ErrorState
          actionLabel="Retry"
          description={uploadError}
          onAction={() => inputRef.current?.click()}
          title="Version upload failed"
        />
      ) : null}

      <VersionsTable items={versions} />
    </div>
  );
}
