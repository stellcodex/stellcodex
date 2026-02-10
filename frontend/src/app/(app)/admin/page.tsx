import Link from "next/link";
import accessControl from "@/security/access-control.source.json";
import { SectionHeader } from "@/components/layout/SectionHeader";
import { EmptyState } from "@/components/ui/StateBlocks";

const TODO = "TODO_REQUIRED";

function isConfigured(value: unknown) {
  return value !== TODO && value !== null && value !== undefined && value !== "";
}

export default function AdminOverviewPage() {
  return (
    <div className="space-y-6">
      <SectionHeader
        title="Overview"
        description="System pulse and operational shortcuts."
        crumbs={[{ label: "Admin", href: "/admin" }, { label: "Overview" }]}
      />

      <div className="grid gap-4 lg:grid-cols-2">
        {(accessControl.kpis?.admin ?? []).some(
          (kpi) => isConfigured(kpi.key) && isConfigured(kpi.endpoint)
        ) ? (
          (accessControl.kpis?.admin ?? []).map((kpi, idx) => (
            <div key={kpi.key || idx} className="rounded-2xl border border-slate-200 bg-white p-5">
              <div className="text-sm font-semibold text-slate-900">{kpi.key}</div>
              <p className="mt-2 text-sm text-slate-600">No data yet.</p>
            </div>
          ))
        ) : (
          <EmptyState
            title="KPI feed not configured"
            description="Define admin KPIs in access-control.source.json."
          />
        )}
        <EmptyState title="System Health" description="No system metrics yet." />
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-5">
        <div className="text-sm font-semibold text-slate-900">Quick Actions</div>
        <div className="mt-3 flex flex-wrap gap-3 text-sm">
          <Link className="text-slate-700 hover:text-slate-900" href="/admin/approvals">
            Go to Approval Queue
          </Link>
          <Link className="text-slate-700 hover:text-slate-900" href="/admin/audit">
            View Audit Logs
          </Link>
        </div>
      </div>
    </div>
  );
}
