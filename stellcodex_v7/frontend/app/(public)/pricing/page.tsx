export default function PricingPage() {
  return (
    <main className="mx-auto max-w-6xl px-6 py-6 sm:py-8">
      <header className="max-w-2xl">
        <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
          Pricing
        </div>
        <h1 className="mt-4 text-xl font-semibold tracking-tight text-slate-900 sm:text-2xl">
          STELLCODEX plans stay simple.
        </h1>
        <p className="mt-3 text-sm text-slate-600">
          The public plan model is locked to Free, Plus, and Pro. The product stays ad-free and workflow-first.
        </p>
      </header>

      <section className="mt-8 grid gap-4 md:grid-cols-3">
        {[
          {
            name: "Free",
            description: "Core upload routing, review, and suite access.",
          },
          {
            name: "Plus",
            description: "Expanded app usage and longer active workflows.",
          },
          {
            name: "Pro",
            description: "Advanced automation and the full suite operating surface.",
          },
        ].map((plan) => (
          <div key={plan.name} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="text-base font-semibold text-slate-900">{plan.name}</div>
            <p className="mt-3 text-sm text-slate-600">{plan.description}</p>
          </div>
        ))}
      </section>

      <section className="mt-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <p className="text-sm text-slate-600">
          Separate mobile packages may expose one focused app, but STELLCODEX remains the canonical product and shared platform core.
        </p>
      </section>
    </main>
  );
}
