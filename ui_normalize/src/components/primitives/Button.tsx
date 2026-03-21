import * as React from "react";

import { cn } from "@/lib/utils";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
}

const variantClassMap: Record<NonNullable<ButtonProps["variant"]>, string> = {
  primary: "border border-[#111111] bg-[#111111] text-white hover:bg-[#1d1d1d]",
  secondary: "border border-[#eeeeee] bg-white text-[var(--foreground-default)] hover:bg-[var(--background-subtle)]",
  ghost: "border border-transparent bg-transparent text-[var(--foreground-default)] hover:bg-[var(--background-subtle)]",
  danger: "border border-[#eeeeee] bg-white text-[var(--foreground-default)] hover:bg-[var(--background-subtle)]",
};

const sizeClassMap: Record<NonNullable<ButtonProps["size"]>, string> = {
  sm: "h-9 px-3 text-sm",
  md: "h-10 px-4 text-sm",
  lg: "h-10 px-4 text-sm",
};

export function Button({
  className,
  variant = "secondary",
  size = "md",
  type = "button",
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      className={cn(
        "inline-flex items-center justify-center rounded-[12px] font-medium transition-colors duration-[var(--motion-base)] ease-[var(--ease-standard)] disabled:cursor-not-allowed disabled:opacity-50",
        variantClassMap[variant],
        sizeClassMap[size],
        className,
      )}
      {...props}
    />
  );
}
