"use client";

import { PublicShareExpiredState } from "@/components/shares/PublicShareExpiredState";
import { PublicShareForbiddenState } from "@/components/shares/PublicShareForbiddenState";
import { PublicShareLayout } from "@/components/shares/PublicShareLayout";
import { PublicShareRevokedState } from "@/components/shares/PublicShareRevokedState";
import { SharePermissionsBadge } from "@/components/shares/SharePermissionsBadge";
import { usePublicShare } from "@/lib/hooks/useShares";

export interface ShareViewerClientProps {
  token: string;
}

function isImage(contentType?: string | null) {
  return Boolean(contentType && contentType.startsWith("image/"));
}

function isDocument(contentType?: string | null) {
  return Boolean(contentType && (contentType.startsWith("text/") || contentType === "application/pdf"));
}

export function ShareViewerClient({ token }: ShareViewerClientProps) {
  const { data, loading, error } = usePublicShare(token);

  if (loading) {
    return (
      <PublicShareLayout title="Resolving shared file">
        <div className="viewer-card">
          <p className="page-copy">Resolving the share link.</p>
        </div>
      </PublicShareLayout>
    );
  }

  if (!data && error) {
    return (
      <PublicShareLayout title="Share unavailable">
        <div className="viewer-card">
          <p className="page-copy">{error}</p>
        </div>
      </PublicShareLayout>
    );
  }

  if (!data || data.status === "expired") return <PublicShareExpiredState />;
  if (data.status === "revoked") return <PublicShareRevokedState />;
  if (data.status === "forbidden" || data.status === "invalid") return <PublicShareForbiddenState />;

  return (
    <PublicShareLayout
      title={data.fileName}
      meta={
        <div className="sc-inline">
          {data.permission ? <SharePermissionsBadge permission={data.permission} /> : null}
          {data.expiresAt ? <span className="page-copy">Expires {data.expiresAt}</span> : null}
        </div>
      }
    >
      <div className="viewer-card">
        {isImage(data.contentType) && data.viewerUrl ? (
          <img src={data.viewerUrl} alt={data.fileName} style={{ width: "100%", height: "auto" }} />
        ) : null}
        {isDocument(data.contentType) && data.viewerUrl ? (
          <iframe title={data.fileName} src={data.viewerUrl} style={{ width: "100%", minHeight: "70vh", border: 0 }} />
        ) : null}
        {!isImage(data.contentType) && !isDocument(data.contentType) ? (
          <p className="page-copy">Viewer unavailable: assembly metadata missing</p>
        ) : null}
      </div>
      <div className="viewer-card">
        <div className="sc-stack">
          <p className="page-copy">Public share token: {token}</p>
          <p className="page-copy">Public file identity: {data.fileId || "Unavailable"}</p>
          {data.downloadUrl ? (
            <a href={data.downloadUrl} target="_blank" rel="noreferrer">
              Download
            </a>
          ) : (
            <p className="page-copy">Download not permitted for this share</p>
          )}
        </div>
      </div>
    </PublicShareLayout>
  );
}
