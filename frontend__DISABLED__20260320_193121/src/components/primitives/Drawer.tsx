"use client";

import * as React from "react";

import { cn } from "@/lib/utils";

export interface DrawerProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  side?: "left" | "right";
  className?: string;
}

export function Drawer({ children, className, onClose, open, side = "right", title }: DrawerProps) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-[var(--z-modal)] bg-black/20">
      <div className="absolute inset-0" onClick={onClose} />
      <aside
        className={cn(
          "absolute top-0 h-full w-full max-w-xl border-l border-[var(--border-default)] bg-[var(--background-surface)] p-6 shadow-[var(--shadow-md)]",
          side === "right" ? "right-0" : "left-0 border-r border-l-0",
          className,
        )}
      >
        <div className="mb-5 flex items-center justify-between">
          <h2 className="text-lg font-semibold">{title}</h2>
          <button className="text-sm text-[var(--foreground-muted)]" onClick={onClose} type="button">
            Close
          </button>
        </div>
        {children}
      </aside>
    </div>
  );
}
