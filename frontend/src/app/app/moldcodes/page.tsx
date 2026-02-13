import { PageHeader } from "@/components/shell/PageHeader";
import { MoldCodesSurface } from "@/components/shell/Surfaces";

export default function AppMoldCodesPage() {
  return (
    <div>
      <PageHeader
        title="MoldCodes"
        searchPlaceholder="Kod veya eleman ara..."
        filters={[
          {
            label: "Kategori",
            options: [
              { label: "Tümü", value: "all" },
              { label: "İtici", value: "itici" },
              { label: "Yolluk", value: "yolluk" },
            ],
          },
          {
            label: "Sıralama",
            options: [
              { label: "En İlgili", value: "rel" },
              { label: "A-Z", value: "az" },
            ],
          },
        ]}
      />
      <MoldCodesSurface />
    </div>
  );
}
