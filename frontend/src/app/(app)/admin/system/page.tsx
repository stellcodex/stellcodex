"use client";

import { useEffect, useState } from "react";
import { Container } from "@/components/ui/Container";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { fetchAdminHealth, fetchAdminQueues, fetchAdminFailed } from "@/services/admin";

type HealthPayload = {
  api: string;
  db: string;
  redis: string;
  rq: string;
  storage?: string;
};

type QueueItem = {
  name: string;
  queued_count: number;
  started_count: number;
  failed_count: number;
};

type FailureItem = {
  id: string;
  job_id?: string | null;
  file_id?: string | null;
  stage: string;
  error_class: string;
  message: string;
  created_at?: string | null;
};

export default function AdminSystemPage() {
  const [health, setHealth] = useState<HealthPayload | null>(null);
  const [queues, setQueues] = useState<QueueItem[]>([]);
  const [failures, setFailures] = useState<FailureItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    Promise.all([fetchAdminHealth(), fetchAdminQueues(), fetchAdminFailed(20)])
      .then(([h, q, f]) => {
        if (!active) return;
        setHealth(h);
        setQueues(q.queues || []);
        setFailures(f.items || []);
      })
      .catch((e: any) => {
        if (!active) return;
        setError(e?.message || "Yönetim verisi alınamadı.");
      });
    return () => {
      active = false;
    };
  }, []);

  return (
    <main className="py-6 sm:py-8">
      <Container>
        <PageHeader title="Yönetim" subtitle="Sistem" />
        {error ? (
          <EmptyState title="Yönetim verisi alınamadı" description={error} />
        ) : (
          <div className="mt-6 grid gap-4 lg:grid-cols-3">
            <Card className="p-4">
              <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Sağlık</div>
              {health ? (
                <div className="mt-3 space-y-1 text-sm text-slate-700">
                  <div>API: {health.api}</div>
                  <div>DB: {health.db}</div>
                  <div>Redis: {health.redis}</div>
                  <div>RQ: {health.rq}</div>
                  {health.storage ? <div>Depolama: {health.storage}</div> : null}
                </div>
              ) : (
                <div className="mt-3 text-sm text-slate-500">Veri yok.</div>
              )}
            </Card>

            <Card className="p-4">
              <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Kuyruklar</div>
              {queues.length ? (
                <div className="mt-3 space-y-2 text-sm text-slate-700">
                  {queues.map((q) => (
                    <div key={q.name} className="rounded-lg border border-slate-100 p-2">
                      <div className="font-medium">{q.name}</div>
                      <div className="text-xs text-slate-500">
                        bekleyen: {q.queued_count} · başlayan: {q.started_count} · başarısız: {q.failed_count}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="mt-3 text-sm text-slate-500">Kuyruk verisi yok.</div>
              )}
            </Card>

            <Card className="p-4">
              <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Hatalar</div>
              {failures.length ? (
                <div className="mt-3 space-y-2 text-xs text-slate-700">
                  {failures.map((f) => (
                    <div key={f.id} className="rounded-lg border border-slate-100 p-2">
                      <div className="font-medium">{f.job_id || f.id}</div>
                      <div className="text-slate-500">{f.stage} · {f.error_class}</div>
                      <div className="mt-1 text-slate-600">{f.message}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="mt-3 text-sm text-slate-500">Hata yok.</div>
              )}
            </Card>
          </div>
        )}
      </Container>
    </main>
  );
}
