import { Button } from "@/components/primitives/Button";

type ErrorStateProps = {
  title: string;
  description?: string;
  retryLabel?: string;
  onRetry?: () => void;
};

export function ErrorState({ title, description, retryLabel, onRetry }: ErrorStateProps) {
  return (
    <div className="sc-error">
      <strong>{title}</strong>
      {description ? <span className="sc-muted">{description}</span> : null}
      {retryLabel && onRetry ? <Button onClick={onRetry}>{retryLabel}</Button> : null}
    </div>
  );
}
