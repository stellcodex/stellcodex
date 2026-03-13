"use client";

import { AppShell } from "@/components/shell/AppShell";
import { Panel } from "@/components/primitives/Panel";
import { Checkbox } from "@/components/primitives/Checkbox";
import { loadSidebarCollapsed, loadUiFlags, saveSidebarCollapsed, saveUiFlags } from "@/lib/store/uiStore";

export default function SettingsPage() {
  const uiFlags = loadUiFlags();
  const sidebarCollapsed = loadSidebarCollapsed();

  return (
    <AppShell title="Settings" subtitle="Real local UI settings only" breadcrumbs={[{ label: "Settings" }]}>
      <div className="sc-grid sc-grid-2">
        <Panel title="Interface">
          <div className="sc-stack">
            <Checkbox
              checked={sidebarCollapsed}
              label="Collapse sidebar by default"
              onChange={(event) => saveSidebarCollapsed(event.target.checked)}
            />
            <Checkbox
              checked={uiFlags.compactTables}
              label="Compact tables"
              onChange={(event) => saveUiFlags({ compactTables: event.target.checked })}
            />
          </div>
        </Panel>
      </div>
    </AppShell>
  );
}
