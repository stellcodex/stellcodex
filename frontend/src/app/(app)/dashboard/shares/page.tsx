import { ListRow } from "@/components/common/ListRow";
import { SectionHeader } from "@/components/layout/SectionHeader";

export default function DashboardSharesPage() {
  return (
    <div className="space-y-6">
      <SectionHeader
        title="Paylaşımlar"
        description="Paylaşım linklerini ve erişimi yönet."
        crumbs={[{ label: "Panel", href: "/dashboard" }, { label: "Paylaşımlar" }]}
      />
      <div className="rounded-2xl border border-slate-200 bg-white p-5">
        <div className="text-sm font-semibold text-slate-900">Son paylaşımlar</div>
        <div className="mt-3 grid gap-3">
          <ListRow title="İnceleme linki" subtitle="2 gün sonra sona erer" />
          <ListRow title="Partner linki" subtitle="aktif" />
          <ListRow title="Süresi dolmuş link" subtitle="iptal" />
        </div>
      </div>
    </div>
  );
}
