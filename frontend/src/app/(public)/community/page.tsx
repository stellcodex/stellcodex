"use client";

import { useEffect, useMemo, useState } from "react";
import accessControl from "@/security/access-control.source.json";
import communityStatic from "@/data/community.static.json";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/StateBlocks";

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
      fetch("/api/community")
        .then(async (res) => {
          if (!res.ok) throw new Error(`Community API failed (${res.status})`);
          return res.json();
        })
        .then((payload) => {
          setData(payload);
          setState("ready");
        })
        .catch((err) => {
          setError(err?.message || "Failed to load community feed");
          setState("error");
        });
      return;
    }
    setState("idle");
  }, [effectiveMode]);

  const items = data?.items ?? [];

  return (
    <main className="mx-auto max-w-6xl px-6 pb-16 pt-14">
      <header className="max-w-2xl">
        <div className="text-xs font-semibold uppercase tracking-[0.2em] text-[#4f6f6b]">
          Library / Community
        </div>
        <h1 className="mt-4 text-3xl font-semibold tracking-tight text-[#0c2a2a] sm:text-4xl">
          Kurasyonlu model galerisi
        </h1>
        <p className="mt-3 text-sm text-[#2c4b49]">
          Paylasilan public modeller burada listelenir. Girişsiz sadece goruntuleme.
        </p>
      </header>

      <section className="mt-8 rounded-3xl border border-[#d7d3c8] bg-white/80 p-6 shadow-sm">
        {effectiveMode === "unset" ? (
          <EmptyState
            title="Community feed not configured"
            description="Select a data source mode in access-control.source.json."
          />
        ) : null}
        {state === "loading" ? <LoadingState lines={4} /> : null}
        {state === "error" ? <ErrorState title="Failed to load" description={error || ""} /> : null}
        {state === "ready" && items.length === 0 ? (
          <EmptyState title="Henüz public icerik yok" description="Ilk paylasim burada gorunecek." />
        ) : null}
        {state === "ready" && items.length > 0 ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {items.map((item, idx) => (
              <div
                key={item.id || idx}
                className="rounded-2xl border border-[#e3dfd3] bg-[#f7f5ef] p-4"
              >
                <div className="text-sm font-semibold text-[#0c2a2a]">
                  {item.title || "Public model"}
                </div>
                <div className="mt-1 text-xs text-[#4f6f6b]">{item.format || "Format"}</div>
                <div className="mt-3 grid place-items-center rounded-xl border border-dashed border-[#d7d3c8] bg-white p-6 text-xs text-[#8a9895]">
                  Thumbnail
                </div>
              </div>
            ))}
          </div>
        ) : null}
      </section>
    </main>
  );
}
