import { LayoutShell } from "@/components/layout/LayoutShell";
import { Card } from "@/components/common/Card";
import { ListRow } from "@/components/common/ListRow";

const categories = [
  { label: "Bağlantı Elemanları", href: "/apps/library/category/fasteners" },
  { label: "Fikstürler", href: "/apps/library/category/fixtures" },
  { label: "Muhafazalar", href: "/apps/library/category/enclosures" },
];

const trending = [
  { id: "m1", title: "Mengene A", subtitle: "1,2k indirme" },
  { id: "m2", title: "Braket 10", subtitle: "940 indirme" },
];

export default function LibraryHomePage() {
  return (
    <LayoutShell>
      <div className="flex flex-col gap-sectionGap">
        <div className="text-fs2 font-semibold">Kütüphane</div>
        <div className="text-fs1 text-muted">Öne çıkanlar</div>
        <div className="flex flex-col gap-cardGap">
          {trending.map((item) => (
            <ListRow key={item.id} title={item.title} subtitle={item.subtitle} href={`/apps/library/model/${item.id}`} />
          ))}
        </div>
        <div className="text-fs1 text-muted">Kategoriler</div>
        <div className="flex flex-wrap gap-cardGap">
          {categories.map((cat) => (
            <Card key={cat.href} title={cat.label} href={cat.href} icon="▣" />
          ))}
        </div>
        <div className="text-fs1 text-muted">Son eklenenler</div>
        <div className="flex flex-col gap-cardGap">
          <ListRow title="Kapak plakası" subtitle="Bugün güncellendi" href="/apps/library/model/m3" />
          <ListRow title="Dişli muhafazası" subtitle="Dün güncellendi" href="/apps/library/model/m4" />
        </div>
      </div>
    </LayoutShell>
  );
}
