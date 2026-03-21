import * as React from "react";

import { Button } from "./Button";

export interface EmptyStateProps {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
}

export function EmptyState({ actionLabel, description, onAction, title }: EmptyStateProps) {
  return (
    <div className="rounded-[var(--radius-lg)] border border-dashed border-[var(--border-default)] bg-[var(--background-subtle)] px-5 py-6 text-sm">
      <div className="font-semibold text-[var(--foreground-strong)]">{title}</div>
      <p className="mt-2 text-[var(--foreground-muted)]">{description}</p>
      {actionLabel && onAction ? (
        <Button className="mt-4" onClick={onAction} size="sm">
          {actionLabel}
        </Button>
      ) : null}
    </div>
  );
}
