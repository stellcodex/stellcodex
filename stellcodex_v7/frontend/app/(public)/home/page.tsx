import Link from "next/link";

export default function PublicHomePage() {
  return (
    <section className="workspace-section">
      <div className="hero-grid">
        <div className="hero-card">
          <div className="eyebrow">Public entry</div>
          <h1 className="display-title">Industrial file work without a fragmented product line.</h1>
          <p className="lede">
            STELLCODEX keeps uploads, projects, sharing, and specialized applications under one calm identity.
          </p>
          <div className="hero-actions">
            <Link className="button button--primary" href="/">
              Open workspace
            </Link>
            <Link className="button button--ghost" href="/upload">
              Upload file
            </Link>
          </div>
        </div>
        <div className="panel-grid">
          <div className="surface-card">
            <h3>Single suite shell</h3>
            <p className="page-copy">The suite does not fork into separate product brands or dark side consoles.</p>
          </div>
          <div className="surface-card">
            <h3>Focused apps</h3>
            <p className="page-copy">3D, 2D, documents, files, projects, and admin stay purpose-built.</p>
          </div>
        </div>
      </div>
    </section>
  );
}
