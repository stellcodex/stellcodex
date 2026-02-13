import { LayoutShell } from "@/components/layout/LayoutShell";
import { EmptyState } from "@/components/common/EmptyState";

export default function ModcodesImportPage() {
  return (
    <LayoutShell>
      <EmptyState
        title="İçe aktar"
        description="CSV/Excel içe aktarma (sadece admin/owner)."
        primaryCta={{ label: "Mod Kodlara dön", href: "/apps/modcodes" }}
      />
    </LayoutShell>
  );
}
