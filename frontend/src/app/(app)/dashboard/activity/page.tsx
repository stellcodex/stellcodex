import { SectionHeader } from "@/components/layout/SectionHeader";
import { EmptyState } from "@/components/ui/StateBlocks";

export default function DashboardActivityPage() {
  return (
    <div className="space-y-6">
      <SectionHeader
        title="Aktivite"
        description="Yükleme, dönüşüm, paylaşım ve görüntüleyici aksiyonları."
        crumbs={[
          { label: "Panel", href: "/dashboard" },
          { label: "Aktivite" },
        ]}
      />

      <div className="rounded-2xl border border-slate-200 bg-white p-5">
        <div className="text-sm font-semibold text-slate-900">Filtreler</div>
        <p className="mt-2 text-sm text-slate-600">
          Olay türü, tarih aralığı, dosya adı.
        </p>
      </div>

      <EmptyState
        title="Henüz bir işlem yok"
        description="Veri kaynakları bağlandığında aktiviteler burada görünecek."
      />
    </div>
  );
}
