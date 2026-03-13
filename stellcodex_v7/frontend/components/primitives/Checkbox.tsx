"use client";

import type { InputHTMLAttributes } from "react";
import { cn } from "@/lib/utils/cn";

export type CheckboxProps = Omit<InputHTMLAttributes<HTMLInputElement>, "type"> & {
  label?: string;
  error?: string | null;
};

export function Checkbox({ className, label, error, ...props }: CheckboxProps) {
  return (
    <label className={cn("sc-checkbox", className)} data-invalid={error ? "true" : "false"}>
      <input {...props} type="checkbox" aria-invalid={error ? "true" : "false"} />
      {label ? <span>{label}</span> : null}
    </label>
  );
}
