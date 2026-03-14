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

export function toggleNodeId(list: string[], nodeId: string) {
  return list.includes(nodeId) ? list.filter((item) => item !== nodeId) : [...list, nodeId];
}
