"use client";

import { useEffect, useState, useTransition } from "react";
import { SectionHeader } from "@/components/layout/SectionHeader";
import { Button } from "@/components/ui/Button";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/StateBlocks";
import { approveAdminApproval, fetchAdminApprovals, rejectAdminApproval } from "@/services/admin";

type ApprovalItem = {
  id: string;
  file_id: string;
  filename?: string | null;
  file_status?: string | null;
  state: string;
  state_label: string;
  approval_required: boolean;
  risk_flags: string[];
  created_at?: string | null;
  updated_at?: string | null;
};

export default function AdminApprovalsPage() {
  const [items, setItems] = useState<ApprovalItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    let alive = true;
    setLoading(true);
    fetchAdminApprovals()
      .then((data) => {
        if (!alive) return;
        setItems(Array.isArray(data?.items) ? data.items : []);
        setError(null);
      })
      .catch((err: any) => {
        if (!alive) return;
        setError(err?.message || "The approval queue could not be loaded.");
      })
      .finally(() => {
        if (!alive) return;
        setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, []);

  function runAction(kind: "approve" | "reject", approvalId: string) {
    setActiveId(approvalId);
    startTransition(() => {
      const op = kind === "approve" ? approveAdminApproval(approvalId) : rejectAdminApproval(approvalId);
      op
        .then((updated) => {
          setItems((prev) =>
            prev.map((item) =>
              item.id === approvalId
                ? {
                    ...item,
                    state: updated.state,
                    state_label: updated.state_label,
                    approval_required: updated.approval_required,
                  }
                : item,
            ),
          );
          setError(null);
        })
        .catch((err: any) => {
          setError(err?.message || `The approval could not be ${kind}d.`);
        })
        .finally(() => {
          setActiveId(null);
        });
    });
  }

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Approval Queue"
        description="Review critical actions before execution."
        crumbs={[{ label: "Admin", href: "/admin" }, { label: "Approvals" }]}
      />

      {loading ? <LoadingState lines={4} /> : null}
      {!loading && error ? <ErrorState title="Approval queue unavailable" description={error} /> : null}

      {!loading && !error && !items.length ? (
        <EmptyState
          title="The approval queue is empty"
          description="No orchestrator session is currently waiting for approval."
        />
      ) : null}

      {!loading && !error && items.length ? (
        <div className="space-y-4">
          {items.map((item) => {
            const busy = isPending && activeId === item.id;
            return (
              <div key={item.id} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                  <div className="space-y-2">
                    <div className="text-sm font-semibold text-slate-900">{item.filename || item.file_id}</div>
                    <div className="text-xs text-slate-500">session: {item.id}</div>
                    <div className="text-xs text-slate-500">file_id: {item.file_id}</div>
                    <div className="flex flex-wrap gap-2 pt-1">
                      <span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-medium text-amber-700">
                        {item.state_label}
                      </span>
                      {item.file_status ? (
                        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-600">
                          file: {item.file_status}
                        </span>
                      ) : null}
                      {item.risk_flags?.map((flag) => (
                        <span key={flag} className="rounded-full bg-rose-50 px-3 py-1 text-xs text-rose-700">
                          {flag}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    <Button variant="primary" disabled={busy} onClick={() => runAction("approve", item.id)}>
                      {busy ? "Working..." : "Approve"}
                    </Button>
                    <Button variant="secondary" disabled={busy} onClick={() => runAction("reject", item.id)}>
                      Reject
                    </Button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}
