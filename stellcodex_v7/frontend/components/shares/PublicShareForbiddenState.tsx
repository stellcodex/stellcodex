import { PublicShareLayout } from "@/components/shares/PublicShareLayout";

export function PublicShareForbiddenState() {
  return (
    <PublicShareLayout title="Access denied">
      <div className="viewer-card">
        <p className="page-copy">Access denied</p>
      </div>
    </PublicShareLayout>
  );
}
