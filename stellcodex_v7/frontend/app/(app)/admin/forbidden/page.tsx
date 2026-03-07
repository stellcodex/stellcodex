import { ErrorState } from "@/components/ui/StateBlocks";

export default function AdminForbiddenPage() {
  return (
    <div className="px-4 py-8 sm:px-6">
      <ErrorState
        title="Yetkin yok"
        description="Bu yönetim alanına erişiminiz yok."
      />
    </div>
  );
}
