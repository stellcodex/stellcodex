import * as React from "react";

import { cn } from "@/lib/utils";

export type InputProps = React.InputHTMLAttributes<HTMLInputElement>;

export const inputClassName =
  "h-10 w-full rounded-[12px] border border-[#eeeeee] bg-white px-3 text-sm text-[var(--foreground-default)] outline-none transition-colors placeholder:text-[var(--foreground-soft)] focus:border-[#dddddd]";

export function Input({ className, ...props }: InputProps) {
  return <input className={cn(inputClassName, className)} {...props} />;
}
