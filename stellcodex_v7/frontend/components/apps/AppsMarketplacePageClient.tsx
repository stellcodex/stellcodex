"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { AppShell } from "@/components/shell/AppShell";
import { listAppsCatalog, type AppsCatalogItem } from "@/services/api";

function normalizeLabel(value: string) {
  return value
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export function AppsMarketplacePageClient() {
  const [items, setItems] = useState<AppsCatalogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const rows = await listAppsCatalog(true);
        if (!active) return;
        setItems(rows);
        setError(null);
      } catch (err) {
        if (!active) return;
        setError(err instanceof Error ? err.message : "Apps katalogu alınamadı.");
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  const grouped = useMemo(() => {
    const map = new Map<string, AppsCatalogItem[]>();
    for (const item of items) {
      const key = item.category || "general";
      const list = map.get(key) || [];
      list.push(item);
      map.set(key, list);
    }
    return [...map.entries()]
      .map(([category, rows]) => [
        category,
        rows.sort((a, b) => {
          if (a.enabled !== b.enabled) return Number(b.enabled) - Number(a.enabled);
          return a.name.localeCompare(b.name);
        }),
      ] as const)
      .sort((a, b) => a[0].localeCompare(b[0]));
  }, [items]);

  return (
    <AppShell section="apps">
      <div className="space-y-4">
        <div className="rounded-2xl border border-[#dbe3ec] bg-white p-5">
          <h1 className="text-2xl font-semibold text-[#10243e]">Apps Marketplace</h1>
          <p className="mt-2 text-sm text-[#4a6076]">
            Tüm modüller aynı Stellcodex ürün kabuğu altında çalışır. Ayrı deploy veya ayrı ürün yoktur.
          </p>
        </div>

        {loading ? <div className="rounded-2xl border border-[#dbe3ec] bg-white p-4 text-sm">Yükleniyor...</div> : null}
        {error ? <div className="rounded-2xl border border-[#ef9a9a] bg-[#fff4f4] p-4 text-sm text-[#8a1f1f]">{error}</div> : null}

        {grouped.map(([category, rows]) => (
          <section key={category} className="rounded-2xl border border-[#dbe3ec] bg-white p-4">
            <h2 className="text-sm font-semibold uppercase tracking-[0.12em] text-[#47607a]">{normalizeLabel(category)}</h2>
            <div className="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              {rows.map((item) => (
                <Link
                  key={item.slug}
                  href={`/apps/${item.slug}`}
                  className={`rounded-xl border p-3 transition ${
                    item.enabled
                      ? "border-[#dbe3ec] bg-[#f8fbff] hover:border-[#9eb9d8]"
                      : "border-[#f1d7a8] bg-[#fffaf1] hover:border-[#d4b073]"
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <strong className="text-sm text-[#12283f]">{item.name}</strong>
                    <div className="flex items-center gap-1">
                      <span className="rounded-md border border-[#d2dde8] bg-white px-2 py-0.5 text-[11px] uppercase text-[#304e6e]">
                        {item.tier}
                      </span>
                      <span
                        className={`rounded-md border px-2 py-0.5 text-[11px] uppercase ${
                          item.enabled
                            ? "border-[#b8e0c0] bg-[#effaf2] text-[#23633a]"
                            : "border-[#f0c27a] bg-[#fff3df] text-[#8a5712]"
                        }`}
                      >
                        {item.enabled ? "enabled" : "disabled"}
                      </span>
                    </div>
                  </div>
                  <p className="mt-2 text-xs text-[#516a80]">{item.required_capabilities.join(" • ")}</p>
                </Link>
              ))}
            </div>
          </section>
        ))}
      </div>
    </AppShell>
  );
}
