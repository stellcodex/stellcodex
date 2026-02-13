import { ListRow } from "@/components/common/ListRow";
import { SectionHeader } from "@/components/layout/SectionHeader";

export default function DashboardProjectsPage() {
  return (
    <div className="space-y-6">
      <SectionHeader
        title="Projeler"
        description="Aktif projelerini takip et ve düzenle."
        crumbs={[{ label: "Panel", href: "/dashboard" }, { label: "Projeler" }]}
      />
      <div className="rounded-2xl border border-slate-200 bg-white p-5">
        <div className="text-sm font-semibold text-slate-900">Son projeler</div>
        <div className="mt-3 grid gap-3">
          <ListRow title="Chassis RevA" subtitle="aktif" />
          <ListRow title="Fixture Set" subtitle="inceleme" />
          <ListRow title="Factory Layout" subtitle="beklemede" />
        </div>
      </div>
    </div>
  );
}
