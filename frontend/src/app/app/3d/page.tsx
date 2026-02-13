import { Suspense } from "react";
import { PageHeader } from "@/components/shell/PageHeader";
import { ViewerModuleSurface } from "@/components/shell/Surfaces";

type App3DPageProps = {
  searchParams?: {
    file?: string;
    name?: string;
  };
};

export default function App3DPage({ searchParams }: App3DPageProps) {
  const fileId = typeof searchParams?.file === "string" ? searchParams.file : undefined;
  const fileName = typeof searchParams?.name === "string" ? searchParams.name : undefined;

  return (
    <div>
      <PageHeader
        title="3D Model"
        searchPlaceholder="3D model ara..."
        primaryAction="Dosya Yükle"
        filters={[
          {
            label: "Dosya Türü",
            options: [
              { label: "Tümü", value: "all" },
              { label: "STEP", value: "step" },
              { label: "IGES", value: "iges" },
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
        <ViewerModuleSurface title="3D model" variant="3d" fileId={fileId} fileName={fileName} />
      </Suspense>
    </div>
  );
}
