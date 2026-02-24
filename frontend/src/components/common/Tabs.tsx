"use client";

import { clsx } from "clsx";
import type { ReactNode } from "react";

export type TabItem = {
  id: string;
  label: string;
  subtitle?: string;
  closable?: boolean;
};

export function Tabs({
  items,
  activeId,
  onSelect,
  onClose,
  rightSlot,
}: {
  items: TabItem[];
  activeId?: string | null;
  onSelect: (id: string) => void;
  onClose?: (id: string) => void;
  rightSlot?: ReactNode;
}) {
  return (
    <div className="flex items-center gap-2 border-b border-slate-200 bg-white px-3 py-2">
      <div className="flex min-w-0 flex-1 gap-2 overflow-x-auto">
        {items.map((tab) => {
          const active = tab.id === activeId;
          return (
            <div
              key={tab.id}
              className={clsx(
                "flex min-w-[180px] items-center gap-2 rounded-xl border px-3 py-2",
                active ? "border-slate-900 bg-slate-900 text-white" : "border-slate-200 bg-slate-50"
              )}
            >
              <button
                className="min-w-0 flex-1 text-left"
                onClick={() => onSelect(tab.id)}
                title={tab.label}
              >
                <div className="truncate text-sm font-medium">{tab.label}</div>
                {tab.subtitle ? (
                  <div className={clsx("truncate text-xs", active ? "text-white/70" : "text-slate-500")}>
                    {tab.subtitle}
                  </div>
                ) : null}
              </button>
              {tab.closable && onClose ? (
                <button
                  onClick={() => onClose(tab.id)}
                  className={clsx(
                    "rounded-md px-1.5 py-0.5 text-xs",
                    active ? "hover:bg-white/10" : "hover:bg-slate-200"
                  )}
                  aria-label={`${tab.label} sekmesini kapat`}
                >
                  ✕
                </button>
              ) : null}
            </div>
          );
        })}
      </div>
      {rightSlot}
    </div>
  );
}

