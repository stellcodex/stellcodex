"use client";

import { useEffect, useMemo, useState } from "react";
import accessControl from "@/security/access-control.source.json";
import communityStatic from "@/data/community.static.json";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/StateBlocks";
import { apiFetchJson } from "@/lib/apiClient";

type CommunityItem = {
  id?: string;
  title?: string;
  format?: string;
  thumbnail?: string;
};

type CommunityPayload = {
  items?: CommunityItem[];
};

const TODO = "TODO_REQUIRED";

function isTodo(value: unknown) {
  return value === TODO || value === null || value === undefined || value === "";
}

export default function CommunityPage() {
  const mode = accessControl.community?.mode;
  const [data, setData] = useState<CommunityPayload | null>(null);
  const [state, setState] = useState<"idle" | "loading" | "ready" | "error">("idle");
  const [error, setError] = useState<string | null>(null);

  const effectiveMode = useMemo(() => {
    if (isTodo(mode)) return "unset";
    return mode;
  }, [mode]);

  useEffect(() => {
    if (effectiveMode === "static") {
      setData(communityStatic as CommunityPayload);
      setState("ready");
      return;
    }
    if (effectiveMode === "api") {
      setState("loading");
      apiFetchJson<CommunityPayload>("/community", undefined, {
        fallbackMessage: "Topluluk verisi alınamadı",
      })
        .then((payload) => {
          setData(payload);
          setState("ready");
        })
        .catch((err) => {
          setError(err?.message || "Topluluk akışı yüklenemedi.");
          setState("error");
        });
      return;
    }
    setState("idle");
  }, [effectiveMode]);

  const items = data?.items ?? [];

  return (
    <main className="mx-auto max-w-6xl px-6 py-6 sm:py-8">
      <header className="max-w-2xl">
        <div className="text-xs font-semibold uppercase tracking-[0.2em] text-[#4f6f6b]">
          Topluluk
        </div>
        <h1 className="mt-4 text-xl font-semibold tracking-tight text-[#0c2a2a] sm:text-2xl">
          Kurasyonlu model galerisi
        </h1>
        <p className="mt-3 text-sm text-[#2c4b49]">
          Paylaşılan açık modeller burada listelenir. Girişsiz sadece görüntüleme.
        </p>
      </header>

      <section className="mt-8 rounded-3xl border border-[#d7d3c8] bg-white/80 p-5 shadow-sm">
        {effectiveMode === "unset" ? (
          <EmptyState
            title="Topluluk akışı yapılandırılmadı"
            description="access-control.source.json içinde veri kaynağını seçin."
          />
        ) : null}
        {state === "loading" ? <LoadingState lines={4} /> : null}
        {state === "error" ? <ErrorState title="Yüklenemedi" description={error || ""} /> : null}
        {state === "ready" && items.length === 0 ? (
          <EmptyState title="Henüz açık içerik yok" description="İlk paylaşım burada görünecek." />
        ) : null}
        {state === "ready" && items.length > 0 ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {items.map((item, idx) => (
              <div
                key={item.id || idx}
                className="rounded-2xl border border-[#e3dfd3] bg-[#f7f5ef] p-4"
              >
                <div className="text-sm font-semibold text-[#0c2a2a]">
                  {item.title || "Açık model"}
                </div>
                <div className="mt-1 text-xs text-[#4f6f6b]">{item.format || "Format"}</div>
                <div className="mt-3 grid place-items-center rounded-xl border border-dashed border-[#d7d3c8] bg-white p-5 text-xs text-[#8a9895]">
                  Önizleme
                </div>
              </div>
            ))}
          </div>
        ) : null}
      </section>
    </main>
  );
}
