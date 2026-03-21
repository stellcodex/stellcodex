import { create } from "zustand";

interface ViewerStoreState {
  selectedNodeIds: string[];
  hiddenNodeIds: string[];
  isolatedNodeId: string | null;
  leftCollapsed: boolean;
  rightCollapsed: boolean;
  searchQuery: string;
  setSelectedNodeIds: (ids: string[]) => void;
  toggleHiddenNode: (id: string) => void;
  setIsolatedNodeId: (id: string | null) => void;
  resetVisibility: () => void;
  setLeftCollapsed: (value: boolean) => void;
  setRightCollapsed: (value: boolean) => void;
  setSearchQuery: (value: string) => void;
}

export const useViewerStore = create<ViewerStoreState>((set) => ({
  selectedNodeIds: [],
  hiddenNodeIds: [],
  isolatedNodeId: null,
  leftCollapsed: false,
  rightCollapsed: false,
  searchQuery: "",
  setSelectedNodeIds: (ids) => set({ selectedNodeIds: ids }),
  toggleHiddenNode: (id) =>
    set((state) => ({
      hiddenNodeIds: state.hiddenNodeIds.includes(id)
        ? state.hiddenNodeIds.filter((entry) => entry !== id)
        : [...state.hiddenNodeIds, id],
    })),
  setIsolatedNodeId: (id) => set({ isolatedNodeId: id }),
  resetVisibility: () => set({ hiddenNodeIds: [], isolatedNodeId: null }),
  setLeftCollapsed: (value) => set({ leftCollapsed: value }),
  setRightCollapsed: (value) => set({ rightCollapsed: value }),
  setSearchQuery: (value) => set({ searchQuery: value }),
}));
