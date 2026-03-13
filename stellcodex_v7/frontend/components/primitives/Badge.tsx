import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils/cn";

export type BadgeProps = HTMLAttributes<HTMLSpanElement> & {
  variant?: "default" | "info" | "success" | "warning" | "danger" | "muted";
};

export function Badge({ className, children, variant = "default", ...props }: BadgeProps) {
  return (
    <span {...props} className={cn("sc-badge", className)} data-variant={variant}>
      {children}
    </span>
  );
}
