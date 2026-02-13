import { SectionHeader } from "@/components/layout/SectionHeader";
import { EmptyState } from "@/components/ui/StateBlocks";

export default function DashboardSettingsPage() {
  return (
    <div className="space-y-6">
      <SectionHeader
        title="Profil ve Ayarlar"
        description="Hesap, güvenlik ve tercih ayarları."
        crumbs={[
          { label: "Panel", href: "/dashboard" },
          { label: "Ayarlar" },
        ]}
      />

      <div className="grid gap-4 lg:grid-cols-2">
        <EmptyState
          title="Profil"
          description="Hesap uç noktaları bağlandığında profil alanları görünecek."
        />
        <EmptyState
          title="Güvenlik"
          description="Kimlik doğrulama entegrasyonları açıldığında güvenlik ayarları görünecek."
        />
        <EmptyState
          title="Tercihler"
          description="Ayarlar tanımlandığında görüntüleyici tercihleri görünecek."
        />
      </div>
    </div>
  );
}
