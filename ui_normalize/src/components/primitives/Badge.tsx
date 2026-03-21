import * as React from "react";

import { cn } from "@/lib/utils";

export interface BadgeProps {
  tone?: "neutral" | "success" | "warning" | "danger" | "info";
  children: React.ReactNode;
  className?: string;
}

const toneClassMap: Record<NonNullable<BadgeProps["tone"]>, string> = {
  neutral: "border border-[#eeeeee] bg-white text-[var(--foreground-default)]",
  success: "border border-[#eeeeee] bg-white text-[var(--foreground-default)]",
  warning: "border border-[#eeeeee] bg-[var(--background-subtle)] text-[var(--foreground-default)]",
  danger: "border border-[#eeeeee] bg-white text-[var(--foreground-default)]",
  info: "border border-[#eeeeee] bg-white text-[var(--foreground-default)]",
};

export function Badge({ children, className, tone = "neutral" }: BadgeProps) {
  return (
    <span className={cn("inline-flex items-center rounded-[999px] px-2.5 py-1 text-xs font-medium", toneClassMap[tone], className)}>
      {children}
    </span>
  );
}
