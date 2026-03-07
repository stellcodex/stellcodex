"use client";

import { useEffect, useState } from "react";
import { SectionHeader } from "@/components/layout/SectionHeader";
import { EmptyState } from "@/components/ui/StateBlocks";
import { fetchAdminAudit } from "@/services/admin";

type AuditItem = {
  id: string;
  event_type: string;
  actor_user_id?: string | null;
  actor_anon_sub?: string | null;
  file_id?: string | null;
  created_at?: string;
};

export default function AdminAuditPage() {
  const [items, setItems] = useState<AuditItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    fetchAdminAudit()
      .then((data) => {
        if (!active) return;
        setItems(data.items || []);
      })
      .catch((e: any) => {
        if (!active) return;
        setError(e?.message || "Denetim verisi alınamadı.");
      });
    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Denetim Kaydı"
        description="Son kritik aksiyonlar."
        crumbs={[{ label: "Yönetim", href: "/admin" }, { label: "Denetim" }]}
      />
      {error ? (
        <EmptyState title="Denetim verisi yok" description={error} />
      ) : (
        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <div className="text-sm font-semibold text-slate-900">Olaylar</div>
          <div className="mt-3 space-y-2 text-sm text-slate-700">
            {items.length ? (
              items.map((a) => (
                <div key={a.id} className="rounded-lg border border-slate-100 p-2">
                  <div className="font-medium">{a.event_type}</div>
                  <div className="text-xs text-slate-500">
                    {a.file_id || "-"} · {a.actor_user_id || a.actor_anon_sub || "-"}
                  </div>
                </div>
              ))
            ) : (
              <div className="text-sm text-slate-500">Denetim kaydı yok.</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
