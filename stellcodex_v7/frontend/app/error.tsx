"use client";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="auth-shell">
      <section className="hero-card" style={{ maxWidth: "720px" }}>
        <div className="eyebrow">Application error</div>
        <h1 className="page-title">The interface hit an unexpected failure.</h1>
        <p className="page-copy">{error.message || "An unknown error occurred."}</p>
        <div className="hero-actions">
          <button className="button button--primary" type="button" onClick={() => reset()}>
            Try again
          </button>
        </div>
      </section>
    </div>
  );
}
