"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/common/Button";
import { getAdminSnapshot } from "@/lib/api";

export function AdminJobDetail({ jobId }: { jobId: string }) {
  const [data, setData] = useState<Awaited<ReturnType<typeof getAdminSnapshot>> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const next = await getAdminSnapshot();
        if (alive) setData(next);
      } catch (e) {
        if (alive) setError(e instanceof Error ? e.message : "Job verisi yüklenemedi.");
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  const job = useMemo(() => data?.jobs.find((j) => j.id === jobId) || null, [data, jobId]);

  if (error) return <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>;
  if (!data) return <div className="rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-600">Yükleniyor...</div>;
  if (!job) return <div className="rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-600">Job bulunamadı.</div>;

  const stages = ["uploaded", "security", "preview", "ready"];
  const activeIndex = stages.indexOf(job.stage);

  return (
    <div className="grid gap-4">
      <div className="rounded-2xl border border-slate-200 bg-white p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="text-xs uppercase tracking-[0.14em] text-slate-500">JobMeta</div>
            <h1 className="mt-2 font-mono text-sm text-slate-900">{job.id}</h1>
            <p className="mt-1 text-sm text-slate-600">
              status={job.status} · stage={job.stage} · progress={job.progress}
            </p>
          </div>
          <Link className="text-sm text-slate-700 hover:text-slate-900" href="/admin">
            Admin&apos;e dön
          </Link>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-4">
        <div className="mb-3 text-sm font-semibold text-slate-800">StageTimeline</div>
        <ol className="grid gap-2">
          {stages.map((stage, idx) => (
            <li key={stage} className="flex items-center gap-3">
              <span
                className={[
                  "grid h-7 w-7 place-items-center rounded-full border text-xs",
                  idx <= activeIndex ? "border-slate-900 bg-slate-900 text-white" : "border-slate-200 bg-white text-slate-400",
                ].join(" ")}
              >
                {idx + 1}
              </span>
              <span className={idx <= activeIndex ? "text-slate-900" : "text-slate-500"}>{stage}</span>
            </li>
          ))}
        </ol>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-4">
        <div className="mb-3 text-sm font-semibold text-slate-800">RiskFlags</div>
        {job.riskFlags && job.riskFlags.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {job.riskFlags.map((flag) => (
              <span key={flag} className="rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs text-amber-700">
                {flag}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-sm text-slate-500">Risk flag yok.</p>
        )}
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-4">
        <div className="mb-3 text-sm font-semibold text-slate-800">ApproveRejectBar</div>
        <div className="flex gap-2">
          <Button variant="primary" onClick={() => window.alert("Mock approve: admin onayı placeholder")}>
            Approve
          </Button>
          <Button variant="danger" onClick={() => window.alert("Mock reject: admin red placeholder")}>
            Reject
          </Button>
        </div>
      </div>
    </div>
  );
}

