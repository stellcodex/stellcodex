import { PublicShareLayout } from "@/components/shares/PublicShareLayout";

export function PublicShareExpiredState() {
  return (
    <PublicShareLayout title="Share expired">
      <div className="viewer-card">
        <p className="page-copy">Share expired</p>
      </div>
    </PublicShareLayout>
  );
}
