import * as React from "react";

import { cn } from "@/lib/utils";

export interface ProductIntroProps {
  eyebrow?: string;
  title: string;
  description: string;
  actions?: React.ReactNode;
  className?: string;
}

export function ProductIntro({ actions, className, description, eyebrow, title }: ProductIntroProps) {
  return (
    <section className={cn("flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between", className)}>
      <div className="max-w-4xl space-y-2">
        {eyebrow ? (
          <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[var(--foreground-soft)]">
            {eyebrow}
          </div>
        ) : null}
        <h2 className="text-2xl font-semibold tracking-[-0.02em] text-[var(--foreground-strong)]">{title}</h2>
        <p className="max-w-3xl text-sm leading-6 text-[var(--foreground-muted)]">{description}</p>
      </div>
      {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
    </section>
  );
}

export interface MetricTileProps {
  label: string;
  value: React.ReactNode;
  detail?: string;
  className?: string;
}

export function MetricTile({ className, detail, label, value }: MetricTileProps) {
  return (
    <div className={cn("rounded-[var(--radius-xl)] border border-[var(--border-default)] bg-[var(--background-surface)] px-4 py-4", className)}>
      <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--foreground-soft)]">{label}</div>
      <div className="mt-3 text-2xl font-semibold tracking-[-0.03em] text-[var(--foreground-strong)]">{value}</div>
      {detail ? <div className="mt-2 text-xs leading-5 text-[var(--foreground-muted)]">{detail}</div> : null}
    </div>
  );
}

export interface MetricGridProps {
  children: React.ReactNode;
  className?: string;
}

export function MetricGrid({ children, className }: MetricGridProps) {
  return <div className={cn("grid gap-3 sm:grid-cols-2 xl:grid-cols-4", className)}>{children}</div>;
}
