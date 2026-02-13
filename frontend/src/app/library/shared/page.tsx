import { PageHeader } from "@/components/shell/PageHeader";
import { LibrarySurface } from "@/components/shell/Surfaces";

export default function LibrarySharedPage() {
  return (
    <div>
      <PageHeader
        title="Paylaşılanlar"
        searchPlaceholder="Paylaşılan dosya ara..."
        primaryAction="Dosya Paylaş"
        filters={[
          {
            label: "Dosya Türü",
            options: [
              { label: "Tümü", value: "all" },
              { label: "3D Model", value: "3d" },
              { label: "2D Çizim", value: "2d" },
            ],
          },
          {
            label: "Sıralama",
            options: [
              { label: "En Popüler", value: "popular" },
              { label: "En Yeniler", value: "new" },
            ],
          },
        ]}
      />
      <LibrarySurface source="paylasilanlar" />
    </div>
  );
}
