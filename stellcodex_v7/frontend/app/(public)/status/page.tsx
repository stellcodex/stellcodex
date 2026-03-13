export const revalidate = 300;

export default function StatusPage() {
  return (
    <section className="workspace-section">
      <div className="page-head">
        <div>
          <h1 className="page-title">Status</h1>
          <p className="page-copy">Fast-refresh public view for release and availability signals.</p>
        </div>
      </div>
      <div className="stat-grid">
        <div className="metric-card">
          <div className="muted">Shell</div>
          <div className="metric-value">OK</div>
        </div>
        <div className="metric-card">
          <div className="muted">API</div>
          <div className="metric-value">OK</div>
        </div>
        <div className="metric-card">
          <div className="muted">Workers</div>
          <div className="metric-value">OK</div>
        </div>
      </div>
    </section>
  );
}
