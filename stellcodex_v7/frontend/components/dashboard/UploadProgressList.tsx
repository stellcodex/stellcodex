import Link from "next/link";
import { Panel } from "@/components/primitives/Panel";
import type { UploadProgressItem } from "@/lib/hooks/useUpload";

type UploadProgressListProps = {
  items: UploadProgressItem[];
  fileHref?: (fileId: string) => string;
  viewerHref?: (fileId: string) => string;
};

export function UploadProgressList({ items, fileHref, viewerHref }: UploadProgressListProps) {
  if (items.length === 0) return null;
  return (
    <Panel title="Upload progress">
      <div className="sc-stack">
        {items.map((item) => {
          const percent =
            item.totalBytes > 0 ? Math.min(100, Math.round((item.bytesUploaded / item.totalBytes) * 100)) : 0;
          return (
            <div key={item.localId} className="sc-panel" data-variant="elevated">
              <div className="sc-panel-body sc-stack">
                <strong>{item.fileName}</strong>
                <span className="sc-muted">
                  {item.status} {item.status === "uploading" ? `${percent}%` : ""}
                </span>
                {item.error ? <span>{item.error}</span> : null}
                {item.fileId ? (
                  <div className="sc-inline">
                    <Link href={fileHref ? fileHref(item.fileId) : `/files/${item.fileId}`}>Open file</Link>
                    <Link href={viewerHref ? viewerHref(item.fileId) : `/files/${item.fileId}/viewer`}>Open viewer</Link>
                  </div>
                ) : null}
              </div>
            </div>
          );
        })}
      </div>
    </Panel>
  );
}
