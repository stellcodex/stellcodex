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
        title="Genel"
        description="Sistem nabzı ve operasyon özetleri."
        crumbs={[{ label: "Yönetim", href: "/admin" }, { label: "Genel" }]}
      />

      <div className="grid gap-4 lg:grid-cols-2">
        {(accessControl.kpis?.admin ?? []).some(
          (kpi) => isConfigured(kpi.key) && isConfigured(kpi.endpoint)
        ) ? (
          (accessControl.kpis?.admin ?? []).map((kpi, idx) => (
            <div key={kpi.key || idx} className="rounded-2xl border border-slate-200 bg-white p-5">
              <div className="text-sm font-semibold text-slate-900">{kpi.key}</div>
              <p className="mt-2 text-sm text-slate-600">Henüz veri yok.</p>
            </div>
          ))
        ) : (
          <EmptyState
            title="KPI kaynağı yapılandırılmadı"
            description="access-control.source.json içinde yönetim KPI'larını tanımlayın."
          />
        )}
        <EmptyState title="Sistem Sağlığı" description="Henüz sistem metriği yok." />
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-5">
        <div className="text-sm font-semibold text-slate-900">Hızlı işlemler</div>
        <div className="mt-3 flex flex-wrap gap-3 text-sm">
          <Link className="text-slate-700 hover:text-slate-900" href="/admin/queue">
            Kuyruklara git
          </Link>
          <Link className="text-slate-700 hover:text-slate-900" href="/admin/audit">
            Denetim kayıtlarını gör
          </Link>
        </div>
      </div>
    </div>
  );
}
