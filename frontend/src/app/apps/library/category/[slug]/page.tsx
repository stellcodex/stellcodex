import { LayoutShell } from "@/components/layout/LayoutShell";
import { ListRow } from "@/components/common/ListRow";

export default function LibraryCategoryPage() {
  return (
    <LayoutShell>
      <div className="flex flex-col gap-sectionGap">
        <div className="text-fs2 font-semibold">Kategori</div>
        <div className="flex flex-col gap-cardGap">
          <ListRow title="Mengene seti" subtitle="Popüler" href="/apps/library/model/c1" />
          <ListRow title="Braket X" subtitle="Yeni" href="/apps/library/model/c2" />
        </div>
      </div>
    </LayoutShell>
  );
}
