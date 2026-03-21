"use client";

import { useEffect, useMemo, useState } from "react";
import { SectionHeader } from "@/components/layout/SectionHeader";
import { EmptyState } from "@/components/ui/StateBlocks";
import { fetchAdminQueues, fetchAdminFailed } from "@/services/admin";

function metric(value: string | number, sub?: string) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4">
      <div className="text-xs uppercase tracking-[0.2em] text-slate-400">Metric</div>
      <div className="mt-2 text-2xl font-semibold text-slate-900">{value}</div>
      {sub ? <div className="mt-1 text-xs text-slate-500">{sub}</div> : null}
    </div>
  );
}

export default function AdminAiPage() {
  const [queues, setQueues] = useState<any[]>([]);
  const [failures, setFailures] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    Promise.all([fetchAdminQueues(), fetchAdminFailed(100)])
      .then(([q, f]) => {
        if (!active) return;
        setQueues(q.queues || []);
        setFailures(f.items || []);
      })
      .catch((e: any) => {
        if (!active) return;
        setError(e?.message || "AI data could not be loaded.");
      });
    return () => {
      active = false;
    };
  }, []);

  const insights = useMemo(() => {
    const queueDepth = queues.reduce((sum, q) => sum + (q.queued_count || 0), 0);
    const failed = failures.length;
    const topFail = failures.reduce((acc: Record<string, number>, f: any) => {
        const key = f.error_class || f.stage || "unknown";
        acc[key] = (acc[key] || 0) + 1;
        return acc;
      }, {} as Record<string, number>);
    const topFailEntries = Object.entries(topFail) as Array<[string, number]>;
    const topFailList = topFailEntries
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .map(([k]) => k);

    const issues: string[] = [];
    const recs: string[] = [];
    if (queueDepth > 20) {
      issues.push("Queue depth is rising.");
      recs.push("Increase worker capacity or batch large jobs.");
    }
    if (failed > 5) {
      issues.push("Conversion failures are increasing.");
      recs.push("Review the most common failure causes by format and route.");
    }
    if (!issues.length) {
      issues.push("No notable issue detected.");
    }
    if (!recs.length) {
      recs.push("The system looks stable. Keep monitoring.");
    }

    return { queueDepth, failed, topFailList, issues, recs };
  }, [queues, failures]);

  return (
    <div className="space-y-6">
      <SectionHeader
        title="AI Insights"
        description="Read-only insights derived from current operational data."
        crumbs={[{ label: "Admin", href: "/admin" }, { label: "AI" }]}
      />
      {error ? (
        <EmptyState title="No AI data" description={error} />
      ) : (
        <>
          <section className="grid gap-4 lg:grid-cols-3">
            {metric(insights.queueDepth, "Queue depth")}
            {metric(insights.failed, "Failed jobs")}
            {metric(insights.topFailList[0] || "-", "Most frequent failure reason")}
          </section>

          <section className="grid gap-4 lg:grid-cols-2">
            <div className="rounded-2xl border border-slate-200 bg-white p-4">
              <div className="text-sm font-semibold text-slate-900">Top issues</div>
              <ul className="mt-3 list-disc pl-4 text-sm text-slate-700">
                {insights.issues.map((i) => (
                  <li key={i}>{i}</li>
                ))}
              </ul>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-4">
              <div className="text-sm font-semibold text-slate-900">Recommendations</div>
              <ul className="mt-3 list-disc pl-4 text-sm text-slate-700">
                {insights.recs.map((i) => (
                  <li key={i}>{i}</li>
                ))}
              </ul>
            </div>
          </section>
        </>
      )}
    </div>
  );
}
