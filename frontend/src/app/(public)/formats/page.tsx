import accessControl from "@/security/access-control.source.json";
import { ALLOWED_FORMATS } from "@/lib/formats.generated";

const TODO = "TODO_REQUIRED";

function renderLimit(value: unknown, suffix = "") {
  if (value === null || value === undefined || value === TODO || value === "") {
    return "Belirtilmedi";
  }
  if (typeof value === "boolean") {
    return value ? "Açık" : "Kapalı";
  }
  return `${value}${suffix}`;
}

export default function FormatsPage() {
  const limits = (accessControl.limits ?? {}) as {
    max_file_size_mb?: number;
    retention_days?: number;
    share_ttl_days_default?: number;
    concurrency_per_user?: number;
    anonymous_upload_enabled?: boolean;
  };

  return (
    <main className="mx-auto max-w-6xl px-6 py-6 sm:py-8">
      <header className="max-w-2xl">
        <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
          Formatlar ve Limitler
        </div>
        <h1 className="mt-4 text-xl font-semibold tracking-tight text-slate-900 sm:text-2xl">
          Desteklenen formatlar ve limitler.
        </h1>
        <p className="mt-3 text-sm text-slate-600">
          Bu sayfa beklentiyi yönetmek için bağlayıcıdır. Detaylı matris:
          <code className="ml-2 rounded bg-slate-100 px-2 py-1">docs/compatibility/formats-matrix.md</code>
        </p>
      </header>

      <section className="mt-8 grid gap-4 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="text-sm font-semibold text-slate-900">Desteklenen Formatlar</div>
          <div className="mt-4 grid gap-3 text-sm text-slate-600">
            <div>
              <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">
                3D
              </div>
              <div className="mt-2">
                {ALLOWED_FORMATS.filter((f) => !["dxf", "pdf", "png", "jpg", "jpeg"].includes(f))
                  .map((f) => f.toUpperCase())
                  .join(" / ")}
              </div>
            </div>
            <div>
              <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">
                2D
              </div>
              <div className="mt-2">DXF / PDF / PNG / JPG</div>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="text-sm font-semibold text-slate-900">Limitler</div>
          <ul className="mt-3 grid gap-2 text-sm text-slate-600">
            <li>Maks. dosya boyutu: {renderLimit(limits.max_file_size_mb, " MB")}</li>
            <li>Maks. saklama süresi: {renderLimit(limits.retention_days, " gün")}</li>
            <li>Paylaşım linki süresi: {renderLimit(limits.share_ttl_days_default, " gün")}</li>
            <li>Eş zamanlı işlem sınırı: {renderLimit(limits.concurrency_per_user)}</li>
            <li>Anonim yükleme: {renderLimit(limits.anonymous_upload_enabled)}</li>
          </ul>
        </div>
      </section>

      <section className="mt-8 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="text-sm font-semibold text-slate-900">Adil Kullanım</div>
        <ul className="mt-3 grid gap-2 text-sm text-slate-600">
          <li>Kötüye kullanım koruması</li>
          <li>Kuyruk sistemi</li>
        </ul>
      </section>
    </main>
  );
}
