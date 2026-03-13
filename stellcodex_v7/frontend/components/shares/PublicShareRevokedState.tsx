import { PublicShareLayout } from "@/components/shares/PublicShareLayout";

export function PublicShareRevokedState() {
  return (
    <PublicShareLayout title="Share unavailable">
      <div className="viewer-card">
        <p className="page-copy">Share unavailable</p>
      </div>
    </PublicShareLayout>
  );
}
