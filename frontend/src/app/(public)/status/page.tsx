"use client";

import { useEffect, useMemo, useState } from "react";
import accessControl from "@/security/access-control.source.json";
import statusStatic from "@/data/status.static.json";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/StateBlocks";
import { apiFetchJson } from "@/lib/apiClient";

type StatusComponent = { name: string; status: string };
type StatusIncident = { id?: string; summary?: string; status?: string; started_at?: string };
type StatusPayload = {
  overall?: string;
  summary?: string;
  updated_at?: string | null;
  components?: StatusComponent[];
  incidents?: StatusIncident[];
};

const TODO = "TODO_REQUIRED";

function isTodo(value: unknown) {
  return value === TODO || value === null || value === undefined || value === "";
}

export default function StatusPage() {
  const mode = accessControl.status?.mode;
  const [data, setData] = useState<StatusPayload | null>(null);
  const [state, setState] = useState<"idle" | "loading" | "ready" | "error">("idle");
  const [error, setError] = useState<string | null>(null);

  const effectiveMode = useMemo(() => {
    if (isTodo(mode)) return "unset";
    return mode;
  }, [mode]);

  useEffect(() => {
    if (effectiveMode === "static") {
      setData(statusStatic as StatusPayload);
      setState("ready");
      return;
    }
    if (effectiveMode === "api") {
      setState("loading");
      apiFetchJson<StatusPayload>("/status", undefined, {
        fallbackMessage: "Durum servisi yanıt vermedi",
      })
        .then((payload) => {
          setData(payload);
          setState("ready");
        })
        .catch((err) => {
          setError(err?.message || "Durum bilgisi alınamadı");
          setState("error");
        });
      return;
    }
    setState("idle");
  }, [effectiveMode]);

  return (
    <main className="mx-auto max-w-6xl px-6 py-6 sm:py-8">
      <header className="max-w-2xl">
        <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
          Durum
        </div>
        <h1 className="mt-4 text-xl font-semibold tracking-tight text-slate-900 sm:text-2xl">
          Sistem durumu
        </h1>
        <p className="mt-3 text-sm text-slate-600">
          Genel durum akışı. Veri kaynağı erişim kontrol dosyasından yönetilir.
        </p>
      </header>

      <section className="mt-8 grid gap-4">
        {effectiveMode === "unset" ? (
          <EmptyState
            title="Durum akışı yapılandırılmadı"
            description="access-control.source.json dosyasında veri kaynağı modunu seçin."
          />
        ) : null}
        {state === "loading" ? <LoadingState lines={4} /> : null}
        {state === "error" ? <ErrorState title="Yüklenemedi" description={error || ""} /> : null}

        {state === "ready" && data ? (
          <>
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="text-sm font-semibold text-slate-900">Genel durum</div>
              <p className="mt-2 text-sm text-slate-600">{data.summary || "Özet bilgisi yok."}</p>
              <div className="mt-2 text-xs text-slate-500">
                Durum: {data.overall || "bilinmiyor"}
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="text-sm font-semibold text-slate-900">Bileşenler</div>
              {data.components && data.components.length > 0 ? (
                <ul className="mt-3 grid gap-2 text-sm text-slate-600">
                  {data.components.map((component) => (
                    <li key={component.name}>
                      {component.name} — {component.status}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="mt-2 text-sm text-slate-600">Henüz bileşen verisi yok.</p>
              )}
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="text-sm font-semibold text-slate-900">Olay geçmişi</div>
              {data.incidents && data.incidents.length > 0 ? (
                <ul className="mt-3 grid gap-2 text-sm text-slate-600">
                  {data.incidents.map((incident, idx) => (
                    <li key={incident.id || idx}>
                      {incident.summary || "Olay"} — {incident.status || "bilinmiyor"}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="mt-2 text-sm text-slate-600">Bildirilmiş olay yok.</p>
              )}
            </div>
          </>
        ) : null}
      </section>
    </main>
  );
}
