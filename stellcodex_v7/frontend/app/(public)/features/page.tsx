export default function FeaturesPage() {
  return (
    <section className="workspace-section">
      <div className="page-head">
        <div>
          <h1 className="page-title">Features</h1>
          <p className="page-copy">One suite, focused applications</p>
        </div>
      </div>
      <div className="card-grid">
        <div className="surface-card">
          <h3>Upload routing</h3>
          <p className="page-copy">Files open in the correct application instead of a generic runner.</p>
        </div>
        <div className="surface-card">
          <h3>Suite services</h3>
          <p className="page-copy">Files, projects, and sharing remain visible across the product.</p>
        </div>
        <div className="surface-card">
          <h3>Focused review</h3>
          <p className="page-copy">3D, 2D, and document flows keep different wording and density.</p>
        </div>
      </div>
    </section>
  );
}
