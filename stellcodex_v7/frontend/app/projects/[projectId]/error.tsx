"use client";

import { ErrorState } from "@/components/primitives/ErrorState";

export default function ProjectDetailError({ reset }: { reset: () => void }) {
  return <ErrorState title="Project unavailable" description="The project detail page could not be rendered." retryLabel="Retry" onRetry={reset} />;
}
