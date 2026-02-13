import { LayoutShell } from "@/components/layout/LayoutShell";
import { ListRow } from "@/components/common/ListRow";
import Link from "next/link";

export default function LibraryCollectionsPage() {
  return (
    <LayoutShell>
      <div className="flex flex-col gap-sectionGap">
        <div className="flex items-center justify-between">
          <div className="text-fs2 font-semibold">Koleksiyonlar</div>
          <Link href="/apps/library/collections/new" className="text-fs0 text-muted">
            Yeni koleksiyon
          </Link>
        </div>
        <div className="flex flex-col gap-cardGap">
          <ListRow title="Standart Parçalar" subtitle="24 öğe" href="/apps/library/collections/standard" />
          <ListRow title="Fikstürler" subtitle="9 öğe" href="/apps/library/collections/fixtures" />
        </div>
      </div>
    </LayoutShell>
  );
}
