export type ViewerOccurrenceNode = {
  nodeId: string;
  label: string;
  occurrencePath: string;
  visible: boolean;
  selected: boolean;
  isolated?: boolean;
  childCount?: number;
  renderBindings?: string[];
  children?: ViewerOccurrenceNode[];
};

export type ViewerSummary = {
  fileId: string;
  status: "loading" | "processing" | "ready" | "failed" | "unavailable";
  hasAssemblyMeta: boolean;
  totalOccurrences: number;
  assemblyTree: ViewerOccurrenceNode[];
  viewerUrl?: string | null;
  viewerKind?: "3d" | "2d" | "doc" | "image" | null;
  unavailableReason?: string | null;
};
