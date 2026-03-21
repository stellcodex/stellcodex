"use client";

import * as React from "react";

import { cn } from "@/lib/utils";

export interface DialogProps {
  open: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: React.ReactNode;
  className?: string;
}

export function Dialog({ children, className, description, onClose, open, title }: DialogProps) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-[var(--z-modal)] flex items-center justify-center bg-black/10 p-4">
      <div className="absolute inset-0" onClick={onClose} />
      <div
        aria-modal="true"
        className={cn(
          "relative z-10 w-full max-w-xl rounded-[12px] border border-[#eeeeee] bg-white p-4",
          className,
        )}
        role="dialog"
      >
        <div className="mb-4 space-y-1">
          <h2 className="text-[18px] font-semibold text-[var(--foreground-strong)]">{title}</h2>
          {description ? <p className="text-sm leading-5 text-[var(--foreground-muted)]">{description}</p> : null}
        </div>
        {children}
      </div>
    </div>
  );
}
