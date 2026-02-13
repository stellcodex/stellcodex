import { LayoutShell } from "@/components/layout/LayoutShell";
import { ListRow } from "@/components/common/ListRow";

export default function LibraryCollectionDetailPage() {
  return (
    <LayoutShell>
      <div className="flex flex-col gap-sectionGap">
        <div className="text-fs2 font-semibold">Koleksiyon</div>
        <div className="flex flex-col gap-cardGap">
          <ListRow title="Mengene A" subtitle="Bugün eklendi" href="/apps/library/model/m1" />
          <ListRow title="Braket 10" subtitle="Dün eklendi" href="/apps/library/model/m2" />
        </div>
      </div>
    </LayoutShell>
  );
}
