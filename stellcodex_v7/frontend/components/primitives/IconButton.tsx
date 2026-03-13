"use client";

import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/utils/cn";

export type IconButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  label: string;
  icon: ReactNode;
  variant?: "primary" | "secondary" | "outline" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
};

export function IconButton({
  className,
  label,
  icon,
  variant = "ghost",
  size = "md",
  ...props
}: IconButtonProps) {
  return (
    <button
      {...props}
      aria-label={label}
      className={cn("sc-button sc-button-icon", className)}
      data-variant={variant}
      data-size={size}
      type={props.type || "button"}
    >
      {icon}
    </button>
  );
}
