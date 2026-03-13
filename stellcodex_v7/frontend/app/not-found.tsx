import Link from "next/link";

export default function NotFound() {
  return (
    <div className="auth-shell">
      <section className="hero-card" style={{ maxWidth: "720px" }}>
        <div className="eyebrow">Not found</div>
        <h1 className="page-title">The requested STELLCODEX surface does not exist.</h1>
        <p className="page-copy">Return to the suite entry and continue inside the canonical workspace shell.</p>
        <div className="hero-actions">
          <Link className="button button--primary" href="/">
            Go home
          </Link>
        </div>
      </section>
    </div>
  );
}
