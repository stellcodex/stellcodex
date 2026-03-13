"use client";

import type { ReactNode } from "react";
import { Button } from "@/components/primitives/Button";

export type DrawerProps = {
  open: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
};

export function Drawer({ open, title, onClose, children }: DrawerProps) {
  if (!open) return null;
  return (
    <div className="sc-drawer-backdrop" role="presentation" onClick={onClose}>
      <aside className="sc-drawer" role="dialog" aria-modal="true" aria-label={title} onClick={(event) => event.stopPropagation()}>
        <header className="sc-dialog-head">
          <strong>{title}</strong>
          <Button variant="ghost" onClick={onClose}>
            Close
          </Button>
        </header>
        <div className="sc-dialog-body">{children}</div>
      </aside>
    </div>
  );
}
