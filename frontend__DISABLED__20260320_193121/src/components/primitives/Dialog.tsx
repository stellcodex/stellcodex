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
    <div className="fixed inset-0 z-[var(--z-modal)] flex items-center justify-center bg-black/20 p-4">
      <div className="absolute inset-0" onClick={onClose} />
      <div
        aria-modal="true"
        className={cn(
          "relative z-10 w-full max-w-xl rounded-[var(--radius-xl)] border border-[var(--border-default)] bg-[var(--background-surface)] p-6 shadow-[var(--shadow-md)]",
          className,
        )}
        role="dialog"
      >
        <div className="mb-5 space-y-1">
          <h2 className="text-xl font-semibold text-[var(--foreground-strong)]">{title}</h2>
          {description ? <p className="text-sm text-[var(--foreground-muted)]">{description}</p> : null}
        </div>
        {children}
      </div>
    </div>
  );
}
