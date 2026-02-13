import { LayoutShell } from "@/components/layout/LayoutShell";
import { ListRow } from "@/components/common/ListRow";

export default function LibraryModelPage() {
  return (
    <LayoutShell>
      <div className="flex flex-col gap-sectionGap">
        <div className="text-fs2 font-semibold">Model Detayı</div>
        <div className="rounded-r2 border-soft bg-surface2 px-cardPad py-cardPad text-fs1 text-muted">
          Önizleme alanı (yer tutucu)
        </div>
        <div className="text-fs1 text-muted">İndirmeler</div>
        <div className="flex flex-col gap-cardGap">
          <ListRow title="GLB" subtitle="3D" />
          <ListRow title="STEP" subtitle="Kaynak" />
          <ListRow title="DXF" subtitle="2D" />
        </div>
      </div>
    </LayoutShell>
  );
}
