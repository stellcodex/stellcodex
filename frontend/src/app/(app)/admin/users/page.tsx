"use client";

import { useEffect, useState } from "react";
import { SectionHeader } from "@/components/layout/SectionHeader";
import { EmptyState } from "@/components/ui/StateBlocks";
import { fetchAdminUsers } from "@/services/admin";

type UserItem = {
  id: string;
  email: string | null;
  role: string;
  is_suspended: boolean;
  created_at?: string;
};

export default function AdminUsersPage() {
  const [users, setUsers] = useState<UserItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    fetchAdminUsers()
      .then((data) => {
        if (!active) return;
        setUsers(data.items || []);
      })
      .catch((e: any) => {
        if (!active) return;
        setError(e?.message || "Kullanıcılar alınamadı.");
      });
    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Kullanıcı Yönetimi"
        description="Roller, durum ve güvenlik aksiyonları."
        crumbs={[{ label: "Yönetim", href: "/admin" }, { label: "Kullanıcılar" }]}
      />
      {error ? (
        <EmptyState title="Kullanıcı verisi yok" description={error} />
      ) : (
        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <div className="text-sm font-semibold text-slate-900">Kullanıcılar</div>
          <div className="mt-3 space-y-2 text-sm text-slate-700">
            {users.length ? (
              users.map((u) => (
                <div key={u.id} className="flex items-center justify-between rounded-lg border border-slate-100 p-2">
                  <div>
                    <div className="font-medium">{u.email || u.id}</div>
                    <div className="text-xs text-slate-500">{u.role}</div>
                  </div>
                  <div className="text-xs text-slate-500">
                    {u.is_suspended ? "Askıda" : "Aktif"}
                  </div>
                </div>
              ))
            ) : (
              <div className="text-sm text-slate-500">Kullanıcı yok.</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
