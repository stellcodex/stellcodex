import { ErrorState } from "@/components/ui/StateBlocks";

export default function NotFound() {
  return (
    <div className="mx-auto max-w-3xl px-6 py-8">
      <ErrorState
        title="Page not found"
        description="The requested page does not exist."
      />
    </div>
  );
}
