import { ErrorState } from "@/components/ui/StateBlocks";

export default function NotFound() {
  return (
    <div className="mx-auto max-w-3xl px-6 py-8">
      <ErrorState
        title="Sayfa bulunamadı"
        description="İstediğiniz sayfa mevcut değil."
      />
    </div>
  );
}
