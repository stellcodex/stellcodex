"use client";

import { ErrorState } from "@/components/primitives/ErrorState";

export default function ProjectsError({ reset }: { reset: () => void }) {
  return <ErrorState title="Projects unavailable" description="The projects page could not be rendered." retryLabel="Retry" onRetry={reset} />;
}
