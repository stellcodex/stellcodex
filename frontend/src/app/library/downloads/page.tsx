import { PageHeader } from "@/components/shell/PageHeader";
import { LibrarySurface } from "@/components/shell/Surfaces";

export default function LibraryDownloadsPage() {
  return (
    <div>
      <PageHeader
        title="İndirilenler"
        searchPlaceholder="İndirilen dosya ara..."
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
      <LibrarySurface source="indirilenler" />
    </div>
  );
}
