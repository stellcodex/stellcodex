"use client";

import { RouteErrorState } from "@/components/states/RouteErrorState";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <RouteErrorState
        actionLabel="Retry"
        description={error.message || "An unexpected route error occurred."}
        onAction={reset}
        title="Route error"
      />
    </main>
  );
}
