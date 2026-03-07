export default function PricingPage() {
  return (
    <main className="mx-auto max-w-6xl px-6 py-6 sm:py-8">
      <header className="max-w-2xl">
        <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
          Fiyatlandırma
        </div>
        <h1 className="mt-4 text-xl font-semibold tracking-tight text-slate-900 sm:text-2xl">
          Yakında
        </h1>
        <p className="mt-3 text-sm text-slate-600">
          Planlar netleştiğinde fiyatlandırma açıklanacaktır.
        </p>
      </header>

      <section className="mt-8 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <p className="text-sm text-slate-600">Plan detayları hazırlanıyor.</p>
      </section>
    </main>
  );
}
