"use client";

import Link from "next/link";
import { clsx } from "clsx";
import type { ButtonHTMLAttributes, AnchorHTMLAttributes, ReactNode } from "react";

type SharedProps = {
  children: ReactNode;
  variant?: "primary" | "ghost" | "danger" | "soft";
  size?: "sm" | "md" | "lg";
  className?: string;
};

type ButtonProps = SharedProps & ButtonHTMLAttributes<HTMLButtonElement> & { href?: never };
type LinkProps = SharedProps &
  AnchorHTMLAttributes<HTMLAnchorElement> & {
    href: string;
  };

function classes(variant: NonNullable<SharedProps["variant"]>, size: NonNullable<SharedProps["size"]>, className?: string) {
  return clsx(
    "inline-flex items-center justify-center rounded-xl border transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400 disabled:cursor-not-allowed disabled:opacity-50",
    {
      primary: "border-slate-900 bg-slate-900 text-white hover:bg-slate-800",
      ghost: "border-transparent bg-transparent text-slate-700 hover:bg-slate-100",
      soft: "border-slate-200 bg-white text-slate-800 hover:bg-slate-50",
      danger: "border-red-200 bg-red-50 text-red-700 hover:bg-red-100",
    }[variant],
    {
      sm: "h-9 px-3 text-sm",
      md: "h-10 px-4 text-sm font-medium",
      lg: "h-12 px-5 text-base font-semibold",
    }[size],
    className
  );
}

export function Button(props: ButtonProps | LinkProps) {
  const variant = props.variant ?? "soft";
  const size = props.size ?? "md";
  if ("href" in props && props.href) {
    const { href, children, className, variant: _v, size: _s, ...rest } = props;
    const anchorProps = rest as AnchorHTMLAttributes<HTMLAnchorElement>;
    return (
      <Link href={href} className={classes(variant, size, className)} {...anchorProps}>
        {children}
      </Link>
    );
  }
  const { children, className, variant: _v, size: _s, ...rest } = props as ButtonProps;
  return (
    <button className={classes(variant, size, className)} {...rest}>
      {children}
    </button>
  );
}
