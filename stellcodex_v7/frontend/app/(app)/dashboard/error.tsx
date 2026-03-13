"use client";

export default function DashboardError({
  error,
  reset,
}: {
  error: Error;
  reset: () => void;
}) {
  return (
    <div className="auth-shell">
      <section className="hero-card">
        <h1 className="page-title">Legacy dashboard redirect failed</h1>
        <p className="page-copy">{error.message}</p>
        <button className="button button--primary" type="button" onClick={() => reset()}>
          Retry
        </button>
      </section>
    </div>
  );
}
