export default function FeaturesPage() {
  return (
    <main className="mx-auto max-w-6xl px-6 py-6 sm:py-8">
      <header className="max-w-2xl">
        <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
          Features
        </div>
        <h1 className="mt-4 text-xl font-semibold tracking-tight text-slate-900 sm:text-2xl">
          A clear line between what it does and what it does not do.
        </h1>
        <p className="mt-3 text-sm text-slate-600">
          This is not CAD. No editing. It is for viewing, review, and controlled sharing.
        </p>
      </header>

      <section className="mt-8 grid gap-4 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="text-sm font-semibold text-slate-900">What it does</div>
          <ul className="mt-3 grid gap-2 text-sm text-slate-600">
            <li>2D and 3D viewing</li>
            <li>Orbit, pan, and zoom</li>
            <li>Section plane controls</li>
            <li>Shareable links</li>
            <li>Multi-format support</li>
          </ul>
        </div>

        <div className="rounded-2xl border border-red-200 bg-red-50 p-5">
          <div className="text-sm font-semibold text-red-700">What it does not do</div>
          <ul className="mt-3 grid gap-2 text-sm text-red-700">
            <li>Does not edit geometry</li>
            <li>Is not parametric CAD</li>
            <li>Does not generate CAM or production output</li>
          </ul>
        </div>
      </section>

      <section className="mt-8 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="text-sm font-semibold text-slate-900">Technical Notes</div>
        <ul className="mt-3 grid gap-2 text-sm text-slate-600">
          <li>Server-side conversion</li>
          <li>Lightweight GLTF outputs</li>
          <li>Browser-based viewer</li>
        </ul>
      </section>
    </main>
  );
}
