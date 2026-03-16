import * as React from "react";

import { cn } from "@/lib/utils";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
}

const variantClassMap: Record<NonNullable<ButtonProps["variant"]>, string> = {
  primary: "bg-[var(--accent-default)] text-[var(--accent-foreground)] hover:bg-[#22262a]",
  secondary: "bg-[var(--background-surface)] text-[var(--foreground-default)] border border-[var(--border-default)] hover:bg-[var(--background-subtle)]",
  ghost: "bg-transparent text-[var(--foreground-default)] hover:bg-[var(--background-subtle)]",
  danger: "bg-[var(--status-danger-fg)] text-white hover:bg-[#8f281a]",
};

const sizeClassMap: Record<NonNullable<ButtonProps["size"]>, string> = {
  sm: "h-9 px-3 text-sm",
  md: "h-10 px-4 text-sm",
  lg: "h-11 px-5 text-base",
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
        "inline-flex items-center justify-center rounded-[var(--radius-md)] font-medium transition-colors duration-[var(--motion-base)] ease-[var(--ease-standard)] disabled:cursor-not-allowed disabled:opacity-50",
        variantClassMap[variant],
        sizeClassMap[size],
        className,
      )}
      {...props}
    />
  );
}
