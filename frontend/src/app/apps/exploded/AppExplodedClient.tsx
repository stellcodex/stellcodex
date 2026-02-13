"use client";

import { LayoutShell } from "@/components/layout/LayoutShell";
import { AppSwitcher } from "@/components/apps/AppSwitcher";
import { ScxContextHeader } from "@/components/apps/ScxContextHeader";
import { EmptyState } from "@/components/common/EmptyState";
import { useScxContext } from "@/components/common/useScxContext";

export default function AppExplodedClient() {
  const context = useScxContext();

  if (!context.scx) {
    return (
      <LayoutShell>
        <EmptyState
          title="Dosya seçili değil"
          description="Patlatma modunu açmak için bir dosya seçin."
          primaryCta={{ label: "Projeler", href: "/projects" }}
          secondaryCta={{ label: "Dosyalar", href: "/files" }}
        />
      </LayoutShell>
    );
  }

  return (
    <LayoutShell>
      <div className="flex flex-col gap-sectionGap">
        <AppSwitcher />
        <ScxContextHeader fileName={context.scx} format="GLB" status="Hazır" />
        <div className="flex flex-col gap-cardGap rounded-r2 border-soft bg-surface px-cardPad py-cardPad">
          <div className="flex items-center gap-sp1">
            <button className="h-btnH rounded-r1 border-soft bg-surface px-sp2 text-fs0">Otomatik</button>
            <button className="h-btnH rounded-r1 border-soft bg-surface px-sp2 text-fs0">Sıfırla</button>
            <button className="h-btnH rounded-r1 border-soft bg-surface px-sp2 text-fs0">Yakala</button>
          </div>
          <div className="rounded-r2 border-soft bg-surface2 px-cardPad py-cardPad text-fs1 text-muted">
            Patlatılmış görünüm (yer tutucu)
          </div>
        </div>
      </div>
    </LayoutShell>
  );
}
