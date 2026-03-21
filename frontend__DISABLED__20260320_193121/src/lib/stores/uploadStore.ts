import { create } from "zustand";

export interface UploadQueueItem {
  localId: string;
  fileName: string;
  progress: number;
  status: "queued" | "uploading" | "success" | "failed";
  fileId?: string;
  error?: string;
}

interface UploadStoreState {
  items: UploadQueueItem[];
  upsertItem: (item: UploadQueueItem) => void;
  clearItem: (localId: string) => void;
  clearAll: () => void;
}

export const useUploadStore = create<UploadStoreState>((set) => ({
  items: [],
  upsertItem: (item) =>
    set((state) => ({
      items: state.items.some((existing) => existing.localId === item.localId)
        ? state.items.map((existing) => (existing.localId === item.localId ? item : existing))
        : [item, ...state.items],
    })),
  clearItem: (localId) =>
    set((state) => ({
      items: state.items.filter((item) => item.localId !== localId),
    })),
  clearAll: () => set({ items: [] }),
}));
