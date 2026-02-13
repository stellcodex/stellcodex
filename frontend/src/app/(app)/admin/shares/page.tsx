"use client";

import { useEffect, useState } from "react";
import { SectionHeader } from "@/components/layout/SectionHeader";
import { EmptyState } from "@/components/ui/StateBlocks";
import { fetchAdminShares } from "@/services/admin";

type ShareItem = {
  id: string;
  file_id: string;
  permission: string;
  expires_at?: string;
  revoked_at?: string | null;
  created_at?: string;
};

export default function AdminSharesPage() {
  const [shares, setShares] = useState<ShareItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    fetchAdminShares()
      .then((data) => {
        if (!active) return;
        setShares(data.items || []);
      })
      .catch((e: any) => {
        if (!active) return;
        setError(e?.message || "Paylaşımlar alınamadı.");
      });
    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Paylaşımlar"
        description="Aktif linkler ve iptaller."
        crumbs={[{ label: "Yönetim", href: "/admin" }, { label: "Paylaşımlar" }]}
      />
      {error ? (
        <EmptyState title="Paylaşım verisi yok" description={error} />
      ) : (
        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <div className="text-sm font-semibold text-slate-900">Paylaşım linkleri</div>
          <div className="mt-3 space-y-2 text-sm text-slate-700">
            {shares.length ? (
              shares.map((s) => (
                <div key={s.id} className="rounded-lg border border-slate-100 p-2">
                  <div className="font-medium">{s.file_id}</div>
                  <div className="text-xs text-slate-500">
                    {s.permission} · süre {s.expires_at || "-"} · {s.revoked_at ? "iptal" : "aktif"}
                  </div>
                </div>
              ))
            ) : (
              <div className="text-sm text-slate-500">Paylaşım yok.</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
