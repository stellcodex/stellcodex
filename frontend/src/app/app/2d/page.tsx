import { Suspense } from "react";
import { PageHeader } from "@/components/shell/PageHeader";
import { ViewerModuleSurface } from "@/components/shell/Surfaces";

type App2DPageProps = {
  searchParams?: {
    file?: string;
    name?: string;
  };
};

export default function App2DPage({ searchParams }: App2DPageProps) {
  const fileId = typeof searchParams?.file === "string" ? searchParams.file : undefined;
  const fileName = typeof searchParams?.name === "string" ? searchParams.name : undefined;

  return (
    <div>
      <PageHeader
        title="2D Çizim"
        searchPlaceholder="2D çizim ara..."
        primaryAction="Dosya Yükle"
        filters={[
          {
            label: "Dosya Türü",
            options: [
              { label: "Tümü", value: "all" },
              { label: "DXF", value: "dxf" },
              { label: "DWG", value: "dwg" },
            ],
          },
          {
            label: "Sıralama",
            options: [
              { label: "En Yeniler", value: "new" },
              { label: "A-Z", value: "az" },
            ],
          },
        ]}
      />
      <Suspense fallback={<div className="rounded-xl border border-[#dce3ee] bg-white p-4 text-sm text-[#64748b]">Yükleniyor...</div>}>
        <ViewerModuleSurface title="2D çizim" variant="2d" fileId={fileId} fileName={fileName} />
      </Suspense>
    </div>
  );
}
