import { ListRow } from "@/components/common/ListRow";
import { AiInsightsPanel } from "@/components/ai/AiInsightsPanel";
import { SectionHeader } from "@/components/layout/SectionHeader";

export default function DashboardOverviewPage() {
  return (
    <div className="space-y-6">
      <SectionHeader
        title="Özet"
        description="Son aktivitenden öne çıkanlar."
        crumbs={[{ label: "Panel", href: "/dashboard" }, { label: "Özet" }]}
      />
      <AiInsightsPanel mode="user" />
      <div className="rounded-2xl border border-slate-200 bg-white p-5">
        <div className="text-sm font-semibold text-slate-900">Öne çıkanlar</div>
        <div className="mt-3 grid gap-3">
          <ListRow title="Son dosya" subtitle="Assembly_A.glb" />
          <ListRow title="Aktif proje" subtitle="Chassis RevA" />
          <ListRow title="Bekleyen paylaşım" subtitle="İnceleme linki" />
        </div>
      </div>
    </div>
  );
}
