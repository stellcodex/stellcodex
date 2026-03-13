"use client";

import { ErrorState } from "@/components/primitives/ErrorState";

export default function SharesError({ reset }: { reset: () => void }) {
  return <ErrorState title="Shares unavailable" description="The shares page could not be rendered." retryLabel="Retry" onRetry={reset} />;
}
