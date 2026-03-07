"use client";

import { Tabs } from "@/components/common/Tabs";
import type { ViewerTab } from "@/lib/stellcodex/view-store";

export function ViewerTabs({
  tabs,
  activeFileId,
  onSelect,
  onClose,
}: {
  tabs: ViewerTab[];
  activeFileId: string | null;
  onSelect: (fileId: string) => void;
  onClose: (fileId: string) => void;
}) {
  return (
    <Tabs
      items={tabs.map((tab) => ({
        id: tab.fileId,
        label: tab.label,
        subtitle: tab.engine,
        closable: true,
      }))}
      activeId={activeFileId}
      onSelect={onSelect}
      onClose={onClose}
    />
  );
}

