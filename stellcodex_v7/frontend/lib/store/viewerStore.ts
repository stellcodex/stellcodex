export type ViewerUiState = {
  selectedNodeIds: string[];
  hiddenNodeIds: string[];
  isolatedNodeId: string | null;
  searchQuery: string;
  leftCollapsed: boolean;
  rightCollapsed: boolean;
};

export const defaultViewerUiState: ViewerUiState = {
  selectedNodeIds: [],
  hiddenNodeIds: [],
  isolatedNodeId: null,
  searchQuery: "",
  leftCollapsed: false,
  rightCollapsed: false,
};
