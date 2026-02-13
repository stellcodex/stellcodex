import { Suspense } from "react";
import { PageHeader } from "@/components/shell/PageHeader";
import { RenderSurface } from "@/components/shell/Surfaces";

type AppRenderPageProps = {
  searchParams?: {
    file?: string;
    name?: string;
  };
};

export default function AppRenderPage({ searchParams }: AppRenderPageProps) {
  const fileId = typeof searchParams?.file === "string" ? searchParams.file : undefined;
  const fileName = typeof searchParams?.name === "string" ? searchParams.name : undefined;

  return (
    <div>
      <PageHeader
        title="Render"
        searchPlaceholder="Render dosyası ara..."
        primaryAction="Dosya Yükle"
        filters={[
          {
            label: "Dosya Türü",
            options: [
              { label: "Tümü", value: "all" },
              { label: "GLB", value: "glb" },
              { label: "STEP", value: "step" },
            ],
          },
          {
            label: "Sıralama",
            options: [
              { label: "En Yeniler", value: "new" },
              { label: "En Yüksek Kalite", value: "hq" },
            ],
          },
        ]}
      />
      <Suspense fallback={<div className="rounded-xl border border-[#dce3ee] bg-white p-4 text-sm text-[#64748b]">Yükleniyor...</div>}>
        <RenderSurface fileId={fileId} fileName={fileName} />
      </Suspense>
    </div>
  );
}
