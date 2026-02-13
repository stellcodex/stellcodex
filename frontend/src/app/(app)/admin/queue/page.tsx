"use client";

import { useEffect, useState } from "react";
import { SectionHeader } from "@/components/layout/SectionHeader";
import { EmptyState } from "@/components/ui/StateBlocks";
import { fetchAdminQueues, fetchAdminFailed } from "@/services/admin";

export default function AdminQueuePage() {
  const [queues, setQueues] = useState<any[]>([]);
  const [failures, setFailures] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    Promise.all([fetchAdminQueues(), fetchAdminFailed(25)])
      .then(([q, f]) => {
        if (!active) return;
        setQueues(q.queues || []);
        setFailures(f.items || []);
      })
      .catch((e: any) => {
        if (!active) return;
        setError(e?.message || "Kuyruk verisi alınamadı.");
      });
    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Kuyruklar"
        description="İşçi kapasitesi ve bekleyen dönüşümler."
        crumbs={[{ label: "Yönetim", href: "/admin" }, { label: "Kuyruklar" }]}
      />
      {error ? (
        <EmptyState title="Kuyruk verisi yok" description={error} />
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          <div className="rounded-2xl border border-slate-200 bg-white p-5">
            <div className="text-sm font-semibold text-slate-900">Kuyruklar</div>
            <div className="mt-3 space-y-2 text-sm text-slate-700">
              {queues.length ? (
                queues.map((q) => (
                  <div key={q.name} className="rounded-lg border border-slate-100 p-2">
                    <div className="font-medium">{q.name}</div>
                    <div className="text-xs text-slate-500">
                      bekleyen: {q.queued_count} · başlayan: {q.started_count} · başarısız: {q.failed_count}
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-sm text-slate-500">Kuyruk verisi yok.</div>
              )}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5">
            <div className="text-sm font-semibold text-slate-900">Başarısız işler</div>
            <div className="mt-3 space-y-2 text-xs text-slate-700">
              {failures.length ? (
                failures.map((f) => (
                  <div key={f.id} className="rounded-lg border border-slate-100 p-2">
                    <div className="font-medium">{f.job_id || f.id}</div>
                    <div className="text-slate-500">{f.stage} · {f.error_class}</div>
                    <div className="mt-1 text-slate-600">{f.message}</div>
                  </div>
                ))
              ) : (
                <div className="text-sm text-slate-500">Başarısız iş yok.</div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
