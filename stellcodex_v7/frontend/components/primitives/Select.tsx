import type { SelectHTMLAttributes } from "react";
import { cn } from "@/lib/utils/cn";

export function Select(props: SelectHTMLAttributes<HTMLSelectElement>) {
  return <select {...props} className={cn("sc-select", props.className)} />;
}
