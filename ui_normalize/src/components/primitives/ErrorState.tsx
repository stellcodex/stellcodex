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
    <div className="rounded-[12px] border border-[#eeeeee] bg-white px-4 py-4 text-sm">
      <div className="font-semibold text-[var(--foreground-strong)]">{title}</div>
      <p className="mt-2 leading-5 text-[var(--foreground-muted)]">{description}</p>
      {actionLabel && onAction ? (
        <Button className="mt-4" onClick={onAction} size="sm" variant="secondary">
          {actionLabel}
        </Button>
      ) : null}
    </div>
  );
}
