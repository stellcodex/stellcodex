export default function FeaturesPage() {
  return (
    <main className="mx-auto max-w-6xl px-6 py-12">
      <header className="max-w-2xl">
        <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
          Features
        </div>
        <h1 className="mt-4 text-3xl font-semibold tracking-tight text-slate-900 sm:text-4xl">
          Ne yapar / ne yapmaz ayrımı net.
        </h1>
        <p className="mt-3 text-sm text-slate-600">
          CAD değiliz. Düzenleme yok. Sadece görüntüleme, inceleme ve paylaşım.
        </p>
      </header>

      <section className="mt-10 grid gap-6 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="text-sm font-semibold text-slate-900">Ne yapar?</div>
          <ul className="mt-3 grid gap-2 text-sm text-slate-600">
            <li>2D / 3D görüntüleme</li>
            <li>Orbit / Pan / Zoom</li>
            <li>Section Plane</li>
            <li>Paylaşılabilir link</li>
            <li>Çok format desteği</li>
          </ul>
        </div>

        <div className="rounded-2xl border border-red-200 bg-red-50 p-6">
          <div className="text-sm font-semibold text-red-700">Ne yapmaz?</div>
          <ul className="mt-3 grid gap-2 text-sm text-red-700">
            <li>Geometri düzenlemez</li>
            <li>Parametrik CAD değildir</li>
            <li>CAM / üretim çıktısı üretmez</li>
          </ul>
        </div>
      </section>

      <section className="mt-8 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="text-sm font-semibold text-slate-900">Teknik Notlar</div>
        <ul className="mt-3 grid gap-2 text-sm text-slate-600">
          <li>Sunucu tarafı dönüşüm</li>
          <li>Hafif GLTF çıktılar</li>
          <li>Tarayıcı tabanlı viewer</li>
        </ul>
      </section>
    </main>
  );
}
