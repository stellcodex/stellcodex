import type { ReactNode } from "react";
import { Button } from "@/components/primitives/Button";

type EmptyStateProps = {
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  icon?: ReactNode;
};

export function EmptyState({ title, description, actionLabel, onAction, icon }: EmptyStateProps) {
  return (
    <div className="sc-empty">
      {icon}
      <strong>{title}</strong>
      {description ? <span className="sc-muted">{description}</span> : null}
      {actionLabel && onAction ? <Button onClick={onAction}>{actionLabel}</Button> : null}
    </div>
  );
}
