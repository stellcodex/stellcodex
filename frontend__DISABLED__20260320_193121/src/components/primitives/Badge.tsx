import * as React from "react";

import { cn } from "@/lib/utils";

export interface BadgeProps {
  tone?: "neutral" | "success" | "warning" | "danger" | "info";
  children: React.ReactNode;
  className?: string;
}

const toneClassMap: Record<NonNullable<BadgeProps["tone"]>, string> = {
  neutral: "bg-[var(--background-subtle)] text-[var(--foreground-default)]",
  success: "bg-[var(--status-success-bg)] text-[var(--status-success-fg)]",
  warning: "bg-[var(--status-warning-bg)] text-[var(--status-warning-fg)]",
  danger: "bg-[var(--status-danger-bg)] text-[var(--status-danger-fg)]",
  info: "bg-[var(--status-info-bg)] text-[var(--status-info-fg)]",
};

export function Badge({ children, className, tone = "neutral" }: BadgeProps) {
  return (
    <span className={cn("inline-flex items-center rounded-[var(--radius-round)] px-2.5 py-1 text-xs font-medium", toneClassMap[tone], className)}>
      {children}
    </span>
  );
}
