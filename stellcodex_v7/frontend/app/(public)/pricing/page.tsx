const PLANS = [
  { name: "Free", note: "Core routing, viewer access, and the shared shell." },
  { name: "Plus", note: "Longer workflows and broader application access." },
  { name: "Pro", note: "Team operations, automation, and the full suite surface." },
];

export default function PricingPage() {
  return (
    <section className="workspace-section">
      <div className="page-head">
        <div>
          <h1 className="page-title">Pricing</h1>
          <p className="page-copy">Plan access maps to suite depth, not to disconnected product names.</p>
        </div>
      </div>
      <div className="card-grid">
        {PLANS.map((plan) => (
          <div key={plan.name} className="surface-card">
            <div className="eyebrow">{plan.name}</div>
            <p className="page-copy">{plan.note}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
