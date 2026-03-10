export default function FeaturesPage() {
  return (
    <main className="mx-auto max-w-6xl px-6 py-6 sm:py-8">
      <header className="max-w-2xl">
        <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
          Features
        </div>
        <h1 className="mt-4 text-xl font-semibold tracking-tight text-slate-900 sm:text-2xl">
          One suite, focused applications, and a clear boundary of responsibility.
        </h1>
        <p className="mt-3 text-sm text-slate-600">
          STELLCODEX is not generic CAD authoring. It is a platform for routing files into the right workflow, reviewing them clearly, and sharing them with control.
        </p>
      </header>

      <section className="mt-8 grid gap-4 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="text-sm font-semibold text-slate-900">What the suite does</div>
          <ul className="mt-3 grid gap-2 text-sm text-slate-600">
            <li>Routes 3D, 2D, and document files into the responsible application</li>
            <li>Keeps 2D, 3D, and document review on different focused surfaces</li>
            <li>Maintains shared files, projects, and share controls across the suite</li>
            <li>Supports controlled review, deep links, and governed sharing</li>
            <li>Expands into engineering apps without changing the core product identity</li>
          </ul>
        </div>

        <div className="rounded-2xl border border-red-200 bg-red-50 p-5">
          <div className="text-sm font-semibold text-red-700">What the suite does not pretend to be</div>
          <ul className="mt-3 grid gap-2 text-sm text-red-700">
            <li>It is not a generic one-screen runner for every task</li>
            <li>It is not a parametric CAD editor</li>
            <li>It does not hide weak flows behind duplicate pages or duplicate buttons</li>
          </ul>
        </div>
      </section>

      <section className="mt-8 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="text-sm font-semibold text-slate-900">Technical Notes</div>
        <ul className="mt-3 grid gap-2 text-sm text-slate-600">
          <li>Route-based application handoff keeps the interface simple</li>
          <li>Low-load public page revalidation keeps Vercel output fresh without request-time rendering</li>
          <li>Browser-based review stays separate from heavy engineering workflows</li>
        </ul>
      </section>
    </main>
  );
}
