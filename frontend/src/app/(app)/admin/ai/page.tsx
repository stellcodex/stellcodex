import { EVENT_NAMES } from "@/data/event-names";

function metric(value: string | number, sub?: string) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4">
      <div className="text-xs uppercase tracking-[0.2em] text-slate-400">Metric</div>
      <div className="mt-2 text-2xl font-semibold text-slate-900">{value}</div>
      {sub ? <div className="mt-1 text-xs text-slate-500">{sub}</div> : null}
    </div>
  );
}

function rulesBasedInsights(data: {
  errorRate: number;
  p95: number;
  queueDepth: number;
  failRate: number;
  rateLimited: number;
}) {
  const issues: string[] = [];
  const recs: string[] = [];

  if (data.errorRate > 1) {
    issues.push("5xx oranı yükseldi.");
    recs.push("API ve worker loglarını kontrol et.");
  }
  if (data.p95 > 2000) {
    issues.push("p95 latency 2s üzeri.");
    recs.push("Queue derinliğini ve worker sayısını kontrol et.");
  }
  if (data.queueDepth > 50) {
    issues.push("Queue derinliği kritik.");
    recs.push("Worker ölçeklemesini artır.");
  }
  if (data.failRate > 5) {
    issues.push("Dönüşüm hata oranı yüksek.");
    recs.push("Top fail reason listesine bak.");
  }
  if (data.rateLimited > 10) {
    issues.push("Rate limit tetiklenmeleri arttı.");
    recs.push("Abuse veya burst yüklemeleri incele.");
  }

  return {
    issues: issues.slice(0, 3),
    recs: recs.slice(0, 3),
  };
}

export default function AdminAiPage() {
  const sample = {
    uptime: "99.9%",
    errorRate: 0.6,
    p95: 840,
    queueDepth: 12,
    activeWorkers: 3,
    avgJob: "48s",
    successRate: "96%",
    topFail: ["Unsupported geometry", "DXF layers missing", "Timeout"],
    uploadsDay: 42,
    formatSplit: "3D 68% / 2D 32%",
    sessionsDay: 120,
    viewerSplit: "3D 71% / 2D 29%",
    sharesDay: 18,
    uniqueViewers: 54,
    securityHits: 0,
    rateLimited: 2,
    permDenied: 1,
  };

  const insights = rulesBasedInsights({
    errorRate: sample.errorRate,
    p95: sample.p95,
    queueDepth: sample.queueDepth,
    failRate: 4,
    rateLimited: sample.rateLimited,
  });

  return (
    <div className="space-y-6">
      <header>
        <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">Admin AI</div>
        <h1 className="mt-2 text-2xl font-semibold text-slate-900">Minimum Metrics</h1>
        <p className="mt-2 text-sm text-slate-600">Otomatik aksiyon yok. Sadece ozet ve oneriler.</p>
      </header>

      <section className="grid gap-4 lg:grid-cols-3">
        {metric(sample.uptime, "Uptime")}
        {metric(`${sample.errorRate}%`, "5xx rate")}
        {metric(`${sample.p95}ms`, "p95 latency")}
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        {metric(sample.queueDepth, "Queue depth")}
        {metric(sample.activeWorkers, "Active workers")}
        {metric(sample.avgJob, "Avg job duration")}
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        {metric(sample.successRate, "Conversion success")}
        {metric(sample.topFail[0], "Top fail reason")}
        {metric(sample.topFail[1], "2nd fail reason")}
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        {metric(sample.uploadsDay, "Uploads/day")}
        {metric(sample.formatSplit, "Format distribution")}
        {metric(sample.sessionsDay, "Viewer sessions/day")}
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        {metric(sample.viewerSplit, "3D vs 2D")}
        {metric(sample.sharesDay, "Shares/day")}
        {metric(sample.uniqueViewers, "Unique viewers")}
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        {metric(sample.securityHits, "Virus hits")}
        {metric(sample.rateLimited, "Rate limited")}
        {metric(sample.permDenied, "Permission denied")}
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-white p-4">
          <div className="text-sm font-semibold text-slate-900">AI Insights</div>
          <div className="mt-3 text-xs text-slate-500">Top 3 issue</div>
          <ul className="mt-2 list-disc pl-4 text-sm text-slate-700">
            {insights.issues.length ? insights.issues.map((i) => <li key={i}>{i}</li>) : <li>Issue yok.</li>}
          </ul>
          <div className="mt-4 text-xs text-slate-500">Top 3 recommendation</div>
          <ul className="mt-2 list-disc pl-4 text-sm text-slate-700">
            {insights.recs.length ? insights.recs.map((i) => <li key={i}>{i}</li>) : <li>Oneri yok.</li>}
          </ul>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-4">
          <div className="text-sm font-semibold text-slate-900">Event Names</div>
          <ul className="mt-3 grid gap-1 text-xs text-slate-600">
            {EVENT_NAMES.map((name) => (
              <li key={name}>{name}</li>
            ))}
          </ul>
        </div>
      </section>
    </div>
  );
}
