"use client";

import { create } from "zustand";
import type { FileKind, ViewerEngine } from "@/lib/stellcodex/types";

export type ViewerTab = {
  id: string;
  fileId: string;
  label: string;
  kind: FileKind;
  engine: ViewerEngine;
};

type ViewerState = {
  tabs: ViewerTab[];
  activeFileId: string | null;
  openTab: (tab: ViewerTab) => void;
  closeTab: (fileId: string) => void;
  setActive: (fileId: string) => void;
};

export const useViewerStore = create<ViewerState>((set) => ({
  tabs: [],
  activeFileId: null,
  openTab: (tab) =>
    set((state) => {
      const exists = state.tabs.find((t) => t.fileId === tab.fileId);
      if (exists) {
        return {
          tabs: state.tabs.map((t) => (t.fileId === tab.fileId ? { ...t, ...tab } : t)),
          activeFileId: tab.fileId,
        };
      }
      return { tabs: [...state.tabs, tab], activeFileId: tab.fileId };
    }),
  closeTab: (fileId) =>
    set((state) => {
      const tabs = state.tabs.filter((t) => t.fileId !== fileId);
      const activeFileId =
        state.activeFileId === fileId ? (tabs[tabs.length - 1]?.fileId ?? null) : state.activeFileId;
      return { tabs, activeFileId };
    }),
  setActive: (fileId) => set({ activeFileId: fileId }),
}));

