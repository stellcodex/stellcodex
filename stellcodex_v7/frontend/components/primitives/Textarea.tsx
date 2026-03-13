import type { TextareaHTMLAttributes } from "react";
import { cn } from "@/lib/utils/cn";

export type TextareaProps = TextareaHTMLAttributes<HTMLTextAreaElement> & {
  error?: string | null;
};

export function Textarea({ className, error, ...props }: TextareaProps) {
  return (
    <textarea
      {...props}
      aria-invalid={error ? "true" : "false"}
      className={cn("sc-textarea", className)}
      data-invalid={error ? "true" : "false"}
    />
  );
}
