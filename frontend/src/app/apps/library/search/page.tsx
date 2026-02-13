import { LayoutShell } from "@/components/layout/LayoutShell";
import { SearchInput } from "@/components/common/SearchInput";
import { ListRow } from "@/components/common/ListRow";

export default function LibrarySearchPage() {
  return (
    <LayoutShell>
      <div className="flex flex-col gap-sectionGap">
        <div className="text-fs2 font-semibold">Kütüphane Arama</div>
        <SearchInput placeholder="Model ara" />
        <div className="flex items-center gap-sp2">
          <button className="h-btnH rounded-r1 border-soft bg-surface px-sp3 text-fs0">Filtre</button>
          <button className="h-btnH rounded-r1 border-soft bg-surface px-sp3 text-fs0">Sırala</button>
        </div>
        <div className="flex flex-col gap-cardGap">
          <ListRow title="Montaj plakası" subtitle="Bağlantı Elemanları" href="/apps/library/model/mt1" />
          <ListRow title="Panel braketi" subtitle="Muhafazalar" href="/apps/library/model/mt2" />
        </div>
      </div>
    </LayoutShell>
  );
}
