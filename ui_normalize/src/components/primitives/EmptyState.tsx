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
    <div className="rounded-[12px] border border-[#eeeeee] bg-white px-4 py-4 text-sm">
      <div className="font-semibold text-[var(--foreground-strong)]">{title}</div>
      <p className="mt-2 leading-5 text-[var(--foreground-muted)]">{description}</p>
      {actionLabel && onAction ? (
        <Button className="mt-4" onClick={onAction} size="sm">
          {actionLabel}
        </Button>
      ) : null}
    </div>
  );
}
