import { SectionHeader } from "@/components/layout/SectionHeader";
import { EmptyState } from "@/components/ui/StateBlocks";

export default function AdminApprovalsPage() {
  return (
    <div className="space-y-6">
      <SectionHeader
        title="Onay Kuyruğu"
        description="Kritik aksiyon incelemesi."
        crumbs={[{ label: "Yönetim", href: "/admin" }, { label: "Onaylar" }]}
      />
      <EmptyState
        title="Onay kuyruğu boş"
        description="Uç nokta bağlandığında onaylar burada görünecek."
      />
    </div>
  );
}
