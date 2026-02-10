import { ErrorState } from "@/components/ui/StateBlocks";

export default function NotFound() {
  return (
    <div className="mx-auto max-w-3xl px-6 py-16">
      <ErrorState
        title="Page not found"
        description="The page you requested does not exist."
      />
    </div>
  );
}
