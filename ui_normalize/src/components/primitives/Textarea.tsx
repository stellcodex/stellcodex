import * as React from "react";

import { cn } from "@/lib/utils";

export type TextareaProps = React.TextareaHTMLAttributes<HTMLTextAreaElement>;

export function Textarea({ className, ...props }: TextareaProps) {
  return (
    <textarea
      className={cn(
        "min-h-28 w-full rounded-[12px] border border-[#eeeeee] bg-white px-3 py-2 text-sm text-[var(--foreground-default)] outline-none transition-colors placeholder:text-[var(--foreground-soft)] focus:border-[#dddddd]",
        className,
      )}
      {...props}
    />
  );
}
