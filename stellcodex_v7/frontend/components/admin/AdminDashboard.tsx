"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getAdminSnapshot } from "@/lib/api";

type AdminSnapshot = Awaited<ReturnType<typeof getAdminSnapshot>>;

export function AdminDashboard() {
  const [data, setData] = useState<AdminSnapshot | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const next = await getAdminSnapshot();
        if (alive) setData(next);
      } catch (e) {
        if (alive) setError(e instanceof Error ? e.message : "Admin verisi yüklenemedi.");
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  if (error) return <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>;
  if (!data) return <div className="rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-600">Yükleniyor...</div>;

  return (
    <div className="grid gap-4">
      <div className="rounded-2xl border border-slate-200 bg-white p-4">
        <h1 className="text-lg font-semibold text-slate-900">Admin</h1>
        <p className="mt-1 text-sm text-slate-600">Jobs, approvals ve sistem bilgisi</p>
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
        <div className="rounded-2xl border border-slate-200 bg-white p-4">
          <div className="mb-3 text-sm font-semibold text-slate-800">JobsTable</div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="text-left text-xs uppercase tracking-[0.12em] text-slate-500">
                <tr>
                  <th className="pb-2 pr-3">Job</th>
                  <th className="pb-2 pr-3">Stage</th>
                  <th className="pb-2 pr-3">Status</th>
                  <th className="pb-2 pr-3">Progress</th>
                  <th className="pb-2">Detay</th>
                </tr>
              </thead>
              <tbody>
                {data.jobs.slice(0, 12).map((job) => (
                  <tr key={job.id} className="border-t border-slate-100">
                    <td className="py-2 pr-3 font-mono text-xs">{job.id}</td>
                    <td className="py-2 pr-3">{job.stage}</td>
                    <td className="py-2 pr-3">{job.status}</td>
                    <td className="py-2 pr-3">%{job.progress}</td>
                    <td className="py-2">
                      <Link className="text-slate-700 hover:text-slate-900 hover:underline" href={`/admin/job/${job.id}`}>
                        Aç
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="grid gap-4">
          <div className="rounded-2xl border border-slate-200 bg-white p-4">
            <div className="mb-2 text-sm font-semibold text-slate-800">PendingApprovals</div>
            {data.pendingApprovals.length === 0 ? (
              <p className="text-sm text-slate-500">Bekleyen approval yok.</p>
            ) : (
              <div className="grid gap-2">
                {data.pendingApprovals.map((job) => (
                  <Link
                    key={job.id}
                    href={`/admin/job/${job.id}`}
                    className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800 hover:bg-amber-100"
                  >
                    {job.id} · {job.riskFlags?.join(", ") || "Risk"}
                  </Link>
                ))}
              </div>
            )}
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-4">
            <div className="mb-2 text-sm font-semibold text-slate-800">SystemInfo</div>
            <div className="grid gap-2 text-sm">
              {Object.entries(data.systemInfo).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between gap-4 rounded-lg bg-slate-50 px-3 py-2">
                  <span className="text-slate-600">{key}</span>
                  <span className="font-medium text-slate-900">{String(value)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

