"use client";

import * as React from "react";

import { cn } from "@/lib/utils";

export interface TabsItem {
  id: string;
  label: string;
  content: React.ReactNode;
}

export interface TabsProps {
  items: TabsItem[];
  defaultValue?: string;
  className?: string;
}

export function Tabs({ className, defaultValue, items }: TabsProps) {
  const [activeTab, setActiveTab] = React.useState(defaultValue ?? items[0]?.id ?? "");
  const activeItem = items.find((item) => item.id === activeTab) ?? items[0];

  return (
    <div className={cn("space-y-4", className)}>
      <div className="flex flex-wrap gap-2 border-b border-[var(--border-muted)] pb-2">
        {items.map((item) => (
          <button
            key={item.id}
            className={cn(
              "rounded-[var(--radius-round)] px-3 py-1.5 text-sm transition-colors",
              item.id === activeItem?.id
                ? "bg-[var(--accent-default)] text-[var(--accent-foreground)]"
                : "bg-[var(--background-subtle)] text-[var(--foreground-muted)] hover:text-[var(--foreground-default)]",
            )}
            onClick={() => setActiveTab(item.id)}
            type="button"
          >
            {item.label}
          </button>
        ))}
      </div>
      <div>{activeItem?.content}</div>
    </div>
  );
}
