export const revalidate = 900;

export default function CommunityPage() {
  return (
    <section className="workspace-section">
      <div className="page-head">
        <div>
          <h1 className="page-title">Community</h1>
          <p className="page-copy">Examples, public feedback loops, and product usage signals.</p>
        </div>
      </div>
      <div className="card-grid">
        <div className="surface-card">
          <h3>Operators</h3>
          <p className="page-copy">Teams need one obvious next step and predictable copy.</p>
        </div>
        <div className="surface-card">
          <h3>Reviewers</h3>
          <p className="page-copy">Trust grows when files, projects, and sharing stay visible in one shell.</p>
        </div>
      </div>
    </section>
  );
}
