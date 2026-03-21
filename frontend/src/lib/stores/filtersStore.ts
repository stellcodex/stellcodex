import { create } from "zustand";

type SortMode = "updated_desc" | "updated_asc" | "name_asc";

interface FiltersStoreState {
  projectSearch: string;
  projectStatus: string;
  sortMode: SortMode;
  setProjectSearch: (value: string) => void;
  setProjectStatus: (value: string) => void;
  setSortMode: (value: SortMode) => void;
}

export const useFiltersStore = create<FiltersStoreState>((set) => ({
  projectSearch: "",
  projectStatus: "all",
  sortMode: "updated_desc",
  setProjectSearch: (value) => set({ projectSearch: value }),
  setProjectStatus: (value) => set({ projectStatus: value }),
  setSortMode: (value) => set({ sortMode: value }),
}));
