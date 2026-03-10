import accessControl from "@/security/access-control.source.json";
import { ALLOWED_FORMATS } from "@/lib/formats.generated";

function isUnset(value: unknown) {
  if (value === null || value === undefined) return true;
  if (typeof value === "string") {
    const normalized = value.trim();
    return normalized.length === 0 || normalized.toLowerCase().startsWith("todo");
  }
  return false;
}

function renderLimit(value: unknown, suffix = "") {
  if (isUnset(value)) {
    return "Not specified";
  }
  if (typeof value === "boolean") {
    return value ? "Enabled" : "Disabled";
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
          Formats and Limits
        </div>
        <h1 className="mt-4 text-xl font-semibold tracking-tight text-slate-900 sm:text-2xl">
          Supported formats and operational limits.
        </h1>
        <p className="mt-3 text-sm text-slate-600">
          This page defines the supported envelope. Full matrix:
          <code className="ml-2 rounded bg-slate-100 px-2 py-1">docs/compatibility/formats-matrix.md</code>
        </p>
      </header>

      <section className="mt-8 grid gap-4 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="text-sm font-semibold text-slate-900">Supported Formats</div>
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
          <div className="text-sm font-semibold text-slate-900">Limits</div>
          <ul className="mt-3 grid gap-2 text-sm text-slate-600">
            <li>Max file size: {renderLimit(limits.max_file_size_mb, " MB")}</li>
            <li>Max retention period: {renderLimit(limits.retention_days, " days")}</li>
            <li>Default share TTL: {renderLimit(limits.share_ttl_days_default, " days")}</li>
            <li>Concurrent processing limit: {renderLimit(limits.concurrency_per_user)}</li>
            <li>Anonymous upload: {renderLimit(limits.anonymous_upload_enabled)}</li>
          </ul>
        </div>
      </section>

      <section className="mt-8 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="text-sm font-semibold text-slate-900">Fair Use</div>
        <ul className="mt-3 grid gap-2 text-sm text-slate-600">
          <li>Abuse protection</li>
          <li>Queue-based processing</li>
        </ul>
      </section>
    </main>
  );
}
