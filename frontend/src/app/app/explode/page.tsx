import { Suspense } from "react";
import { PageHeader } from "@/components/shell/PageHeader";
import { ViewerModuleSurface } from "@/components/shell/Surfaces";

type AppExplodePageProps = {
  searchParams?: {
    file?: string;
    name?: string;
  };
};

export default function AppExplodePage({ searchParams }: AppExplodePageProps) {
  const fileId = typeof searchParams?.file === "string" ? searchParams.file : undefined;
  const fileName = typeof searchParams?.name === "string" ? searchParams.name : undefined;

  return (
    <div>
      <PageHeader
        title="Patlatma"
        searchPlaceholder="Montaj ara..."
        primaryAction="Dosya Yükle"
        filters={[
          {
            label: "Dosya Türü",
            options: [
              { label: "Tümü", value: "all" },
              { label: "STEP", value: "step" },
            ],
          },
          {
            label: "Sıralama",
            options: [
              { label: "En Yeniler", value: "new" },
              { label: "En Büyük", value: "large" },
            ],
          },
        ]}
      />
      <Suspense fallback={<div className="rounded-xl border border-[#dce3ee] bg-white p-4 text-sm text-[#64748b]">Yükleniyor...</div>}>
        <ViewerModuleSurface title="Patlatma" variant="explode" fileId={fileId} fileName={fileName} />
      </Suspense>
    </div>
  );
}
