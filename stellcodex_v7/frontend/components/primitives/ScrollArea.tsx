import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils/cn";

export type ScrollAreaProps = HTMLAttributes<HTMLDivElement>;

export function ScrollArea({ className, children, ...props }: ScrollAreaProps) {
  return (
    <div {...props} className={cn("sc-scroll-area", className)}>
      {children}
    </div>
  );
}
