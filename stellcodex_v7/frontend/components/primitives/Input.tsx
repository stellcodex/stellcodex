import type { InputHTMLAttributes } from "react";
import { cn } from "@/lib/utils/cn";

export type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  error?: string | null;
};

export function Input({ className, error, ...props }: InputProps) {
  return (
    <input
      {...props}
      aria-invalid={error ? "true" : "false"}
      className={cn("sc-input", className)}
      data-invalid={error ? "true" : "false"}
    />
  );
}
