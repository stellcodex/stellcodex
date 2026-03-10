import { ListRow } from "@/components/common/ListRow";
import { SectionHeader } from "@/components/layout/SectionHeader";

export default function DashboardSharesPage() {
  return (
    <div className="space-y-6">
      <SectionHeader
        title="Shares"
        description="Manage share links and access."
        crumbs={[{ label: "Dashboard", href: "/dashboard" }, { label: "Shares" }]}
      />
      <div className="rounded-2xl border border-slate-200 bg-white p-5">
        <div className="text-sm font-semibold text-slate-900">Recent shares</div>
        <div className="mt-3 grid gap-3">
          <ListRow title="Review link" subtitle="expires in 2 days" />
          <ListRow title="Partner link" subtitle="active" />
          <ListRow title="Expired link" subtitle="revoked" />
        </div>
      </div>
    </div>
  );
}
