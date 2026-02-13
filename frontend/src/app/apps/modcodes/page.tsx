import { LayoutShell } from "@/components/layout/LayoutShell";
import { SearchInput } from "@/components/common/SearchInput";
import { Card } from "@/components/common/Card";

const items = [
  { id: "mx1", label: "Valf Gövdesi" },
  { id: "mx2", label: "Pompa Şasesi" },
  { id: "mx3", label: "Şanzıman" },
];

export default function ModcodesPage() {
  return (
    <LayoutShell>
      <div className="flex flex-col gap-sectionGap">
        <div className="text-fs2 font-semibold">Mod Kodları</div>
        <SearchInput placeholder="Ara" />
        <div className="flex items-center gap-sp2">
          <button className="h-btnH rounded-r1 border-soft bg-surface px-sp3 text-fs0">Filtreler</button>
          <button className="h-btnH rounded-r1 border-soft bg-surface px-sp3 text-fs0">İçe aktar</button>
        </div>
        <div className="flex flex-wrap gap-cardGap">
          {items.map((item) => (
            <Card key={item.id} title={item.label} href={`/apps/modcodes/${item.id}`} icon="▤" />
          ))}
        </div>
      </div>
    </LayoutShell>
  );
}
