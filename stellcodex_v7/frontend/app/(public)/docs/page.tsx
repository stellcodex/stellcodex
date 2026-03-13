export const revalidate = 1800;

export default function DocsPage() {
  return (
    <section className="workspace-section">
      <div className="page-head">
        <div>
          <h1 className="page-title">Docs</h1>
          <p className="page-copy">Reference material for routing, file workflows, and application surfaces.</p>
        </div>
      </div>
      <div className="panel">
        <h3>Current direction</h3>
        <p className="page-copy">
          The suite entry stays singular. Uploads, projects, library flows, and focused applications connect through the same shell.
        </p>
      </div>
    </section>
  );
}
