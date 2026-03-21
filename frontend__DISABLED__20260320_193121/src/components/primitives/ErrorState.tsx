import * as React from "react";

import { Button } from "./Button";

export interface ErrorStateProps {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
}

export function ErrorState({ actionLabel, description, onAction, title }: ErrorStateProps) {
  return (
    <div className="rounded-[var(--radius-lg)] border border-[var(--status-danger-fg)]/20 bg-[var(--status-danger-bg)] px-5 py-6 text-sm">
      <div className="font-semibold text-[var(--status-danger-fg)]">{title}</div>
      <p className="mt-2 text-[var(--foreground-muted)]">{description}</p>
      {actionLabel && onAction ? (
        <Button className="mt-4" onClick={onAction} size="sm" variant="danger">
          {actionLabel}
        </Button>
      ) : null}
    </div>
  );
}
