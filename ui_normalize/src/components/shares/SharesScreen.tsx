"use client";

import * as React from "react";

import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { Input } from "@/components/primitives/Input";
import { Select } from "@/components/primitives/Select";
import { PageHeader } from "@/components/shell/PageHeader";
import { ShareDialog } from "@/components/shares/ShareDialog";
import { RouteErrorState } from "@/components/states/RouteErrorState";
import { RouteLoadingState } from "@/components/states/RouteLoadingState";
import { listFiles } from "@/lib/api/files";
import { useShares } from "@/lib/hooks/useShares";
import { mapFileRecord } from "@/lib/mappers/fileMappers";

import { ShareTable } from "./ShareTable";

export function SharesScreen() {
  const { shares, loading, error, refresh, copyLink, openLink, revoke, create } = useShares();
  const [query, setQuery] = React.useState("");
  const [createDialogOpen, setCreateDialogOpen] = React.useState(false);
  const [selectedFileId, setSelectedFileId] = React.useState("");
  const [files, setFiles] = React.useState<Array<{ fileId: string; originalName: string }>>([]);

  React.useEffect(() => {
    void listFiles()
      .then((rows) => {
        const mapped = rows.map(mapFileRecord);
        setFiles(mapped.map((file) => ({ fileId: file.fileId, originalName: file.originalName })));
        setSelectedFileId((current) => current || mapped[0]?.fileId || "");
      })
      .catch(() => undefined);
  }, []);

  if (loading) return <RouteLoadingState title="Loading shares" />;
  if (error) return <RouteErrorState actionLabel="Retry" description={error} onAction={() => void refresh()} title="Shares unavailable" />;

  const filteredShares = shares.filter((share) => {
    const normalizedQuery = query.trim().toLowerCase();
    if (!normalizedQuery) return true;
    return share.token.toLowerCase().includes(normalizedQuery) || share.fileId?.toLowerCase().includes(normalizedQuery);
  });

  return (
    <div className="space-y-6">
      <PageHeader subtitle="Public links" title="Shares" />
      <Card title="Create Share">
        <div className="space-y-3">
          <Select onChange={(event) => setSelectedFileId(event.target.value)} value={selectedFileId}>
            {files.length === 0 ? <option value="">No files available</option> : null}
            {files.map((file) => (
              <option key={file.fileId} value={file.fileId}>
                {file.originalName} · {file.fileId}
              </option>
            ))}
          </Select>
          <Button onClick={() => setCreateDialogOpen(true)} size="sm" type="button" variant="primary">
            Create share
          </Button>
        </div>
      </Card>
      <Card title="Share Inventory">
        <div className="mb-4">
          <Input onChange={(event) => setQuery(event.target.value)} placeholder="Search token or file_id" value={query} />
        </div>
        <ShareTable onCopy={copyLink} onOpen={openLink} onRevoke={revoke} shares={filteredShares} />
      </Card>
      <ShareDialog
        onClose={() => setCreateDialogOpen(false)}
        onCreate={async (permission, expiresInSeconds) => {
          if (!selectedFileId) throw new Error("Select a file before creating a share.");
          await create(selectedFileId, permission, expiresInSeconds);
        }}
        open={createDialogOpen}
      />
    </div>
  );
}
