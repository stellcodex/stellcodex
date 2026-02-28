"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { type LibraryItem, getLibraryFeed } from "@/services/api";

export default function LibraryPage() {
  const [items, setItems] = useState<LibraryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    getLibraryFeed({ sort: "new", page: 1, page_size: 24 })
      .then((data) => {
        if (!alive) return;
        setItems(data.items || []);
      })
      .catch((err) => {
        if (!alive) return;
        setError(err?.message || "Library feed alınamadı.");
      })
      .finally(() => {
        if (alive) setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, []);

  return (
    <div className="space-y-4">
      <header className="rounded-2xl border border-slate-200 bg-white p-4">
        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Library</div>
        <h1 className="mt-1 text-xl font-semibold text-slate-900">Public Model Feed</h1>
        <p className="mt-1 text-sm text-slate-600">Topluluk tarafından yayınlanan modeller.</p>
      </header>

      {loading ? <div className="rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-500">Yükleniyor...</div> : null}
      {error ? <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div> : null}

      {!loading && !error ? (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((item) => (
            <article key={item.id} className="rounded-2xl border border-slate-200 bg-white p-3">
              <div className="aspect-[16/10] overflow-hidden rounded-xl bg-slate-100">
                {item.cover_thumb ? (
                  <img src={item.cover_thumb} alt={item.title} className="h-full w-full object-cover" />
                ) : (
                  <div className="grid h-full place-items-center text-xs text-slate-500">No thumbnail</div>
                )}
              </div>
              <div className="mt-3">
                <div className="truncate text-sm font-semibold text-slate-900">{item.title}</div>
                <div className="mt-1 text-xs text-slate-500">{item.tags?.join(", ") || "etiket yok"}</div>
              </div>
              <div className="mt-3 flex items-center justify-between">
                <Link href={`/m/${item.slug}`} className="rounded-lg border border-slate-300 bg-white px-2 py-1 text-xs font-semibold text-slate-700">
                  Aç
                </Link>
                {item.share_url ? (
                  <Link href={item.share_url} className="rounded-lg border border-slate-300 bg-slate-50 px-2 py-1 text-xs font-semibold text-slate-700">
                    Share
                  </Link>
                ) : null}
              </div>
            </article>
          ))}
        </div>
      ) : null}
    </div>
  );
}

