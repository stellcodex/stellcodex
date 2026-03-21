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

export default function CommunityPage() {
  const mode = accessControl.community?.mode;
  const [data, setData] = useState<CommunityPayload | null>(null);
  const [state, setState] = useState<"idle" | "loading" | "ready" | "error">("idle");
  const [error, setError] = useState<string | null>(null);

  const effectiveMode = useMemo(() => {
    if (mode === "static" || mode === "api") return mode;
    return "unset";
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
        fallbackMessage: "Community data could not be loaded",
      })
        .then((payload) => {
          setData(payload);
          setState("ready");
        })
        .catch((err) => {
          setError(err?.message || "The community feed could not be loaded.");
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
          Community
        </div>
        <h1 className="mt-4 text-xl font-semibold tracking-tight text-[#0c2a2a] sm:text-2xl">
          Curated model gallery
        </h1>
        <p className="mt-3 text-sm text-[#2c4b49]">
          Open shared models are listed here. Anonymous access stays read-only.
        </p>
      </header>

      <section className="mt-8 rounded-3xl border border-[#d7d3c8] bg-white/80 p-5 shadow-sm">
        {effectiveMode === "unset" ? (
          <EmptyState
            title="Community feed is not configured"
            description="Select the data source in access-control.source.json."
          />
        ) : null}
        {state === "loading" ? <LoadingState lines={4} /> : null}
        {state === "error" ? <ErrorState title="Could not load" description={error || ""} /> : null}
        {state === "ready" && items.length === 0 ? (
          <EmptyState title="No public content yet" description="The first shared item will appear here." />
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
                <div className="mt-3 grid place-items-center rounded-xl border border-dashed border-[#d7d3c8] bg-white p-5 text-xs text-[#8a9895]">
                  Preview
                </div>
              </div>
            ))}
          </div>
        ) : null}
      </section>
    </main>
  );
}
