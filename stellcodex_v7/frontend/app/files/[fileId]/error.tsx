"use client";

import { ErrorState } from "@/components/primitives/ErrorState";

export default function FileDetailError({ reset }: { reset: () => void }) {
  return <ErrorState title="File unavailable" description="The file detail page could not be rendered." retryLabel="Retry" onRetry={reset} />;
}
