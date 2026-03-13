type LoadingSkeletonProps = {
  label?: string;
};

export function LoadingSkeleton({ label = "Loading..." }: LoadingSkeletonProps) {
  return (
    <div className="sc-loading">
      <strong>{label}</strong>
      <span className="sc-muted">Please wait while the latest data is loaded.</span>
    </div>
  );
}
