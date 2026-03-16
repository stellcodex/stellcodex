import { RouteEmptyState } from "@/components/states/RouteEmptyState";

export default function NotFoundPage() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <RouteEmptyState
        description="The requested STELLCODEX route does not exist."
        title="Route not found"
      />
    </main>
  );
}
