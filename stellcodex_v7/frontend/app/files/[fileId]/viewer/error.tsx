"use client";

import { ViewerErrorState } from "@/components/viewer/ViewerErrorState";

export default function FileViewerError({ reset }: { reset: () => void }) {
  return <ViewerErrorState description="The viewer page could not be rendered." onRetry={reset} />;
}
