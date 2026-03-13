"use client";

import { useState } from "react";
import { DxfViewer } from "@/components/viewer/DxfViewer";
import { ThreeViewer } from "@/components/viewer/ThreeViewer";
import type { ViewerSummary } from "@/lib/contracts/viewer";
import { ViewerErrorState } from "@/components/viewer/ViewerErrorState";
import { ViewerUnavailableState } from "@/components/viewer/ViewerUnavailableState";

export interface ViewerCanvasProps {
  fileId: string;
  viewer: ViewerSummary;
  fitRequestKey?: number;
}

export function ViewerCanvas({ fileId, viewer, fitRequestKey = 0 }: ViewerCanvasProps) {
  const [fitKey, setFitKey] = useState(0);

  if (viewer.status === "unavailable") {
    return <ViewerUnavailableState description={viewer.unavailableReason || "Viewer unavailable"} />;
  }

  if (viewer.status === "failed") {
    return <ViewerErrorState description="Viewer failed to initialize" onRetry={() => setFitKey((value) => value + 1)} />;
  }

  if (viewer.viewerKind === "2d") {
    return (
      <div className="sc-viewer-canvas sc-panel">
        <DxfViewer fileId={fileId} fitRequestKey={fitRequestKey || fitKey} background="light" />
      </div>
    );
  }

  if (viewer.viewerKind === "image" && viewer.viewerUrl) {
    return (
      <div className="sc-viewer-canvas sc-panel">
        <img src={viewer.viewerUrl} alt="Shared preview" style={{ width: "100%", height: "100%", objectFit: "contain" }} />
      </div>
    );
  }

  if (viewer.viewerKind === "doc" && viewer.viewerUrl) {
    return (
      <div className="sc-viewer-canvas sc-panel">
        <iframe title="Document preview" src={viewer.viewerUrl} style={{ width: "100%", height: "100%", border: 0 }} />
      </div>
    );
  }

  if (viewer.viewerUrl) {
    return (
      <div className="sc-viewer-canvas sc-panel">
        <ThreeViewer url={viewer.viewerUrl} fitRequestKey={fitRequestKey || fitKey} />
      </div>
    );
  }

  return <ViewerUnavailableState description="Viewer unavailable" />;
}
