import { LayoutShell } from "@/components/layout/LayoutShell";
import { ListRow } from "@/components/common/ListRow";

export default function ModcodesDetailPage() {
  return (
    <LayoutShell>
      <div className="flex flex-col gap-sectionGap">
        <div className="text-fs2 font-semibold">Mod Kod Detayı</div>
        <div className="rounded-r2 border-soft bg-surface2 px-cardPad py-cardPad text-fs1 text-muted">
          Konfigüratör (params_schema yer tutucu)
        </div>
        <div className="text-fs1 text-muted">İndirmeler</div>
        <div className="flex flex-col gap-cardGap">
          <ListRow title="GLB" subtitle="3D" />
          <ListRow title="STEP" subtitle="Kaynak" />
        </div>
        <button className="h-btnH rounded-r1 bg-accent px-sp3 text-fs1 font-medium text-bg">
          Projeye ekle
        </button>
      </div>
    </LayoutShell>
  );
}
