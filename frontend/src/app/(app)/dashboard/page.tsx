"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { listFiles, FileItem } from "@/services/api";

const statusLabel: Record<string, string> = {
  pending: "Yukleme bekliyor",
  queued: "Kuyrukta",
  processing: "Isleniyor",
  ready: "Hazir",
  failed: "Basarisiz",
};

export default function DashboardPage() {
  const [items, setItems] = useState<FileItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const data = await listFiles();
        if (!cancelled) setItems(data);
      } catch (e: any) {
        if (!cancelled) setError((e?.message || "Dosyalar yuklenemedi") + ". Tekrar deneyin.");
      }
    };
    void load();
    const id = setInterval(load, 6000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  return (
    <main className="mx-auto max-w-6xl px-6 pb-16 pt-10">
      <header>
        <div className="text-xs font-semibold uppercase tracking-[0.2em] text-[#4f6f6b]">Dashboard</div>
        <h1 className="mt-3 text-2xl font-semibold text-[#0c2a2a]">Durum</h1>
        <p className="mt-2 text-sm text-[#2c4b49]">Dosyalar ve paylasimlarin tek ekrani.</p>
      </header>

      <section className="mt-6 rounded-2xl border border-[#d7d3c8] bg-white/80 p-5">
        <div className="text-sm font-semibold text-[#0c2a2a]">Dosyalar</div>
        <div className="mt-4 grid gap-3">
          {error ? <div className="text-sm text-red-600">{error}</div> : null}
          {items.length === 0 ? (
            <div className="text-center text-sm text-[#2c4b49]">
              <div className="text-2xl">⭘</div>
              <div className="mt-2">Henüz dosya yok. Yukleme yap.</div>
              <Link
                href="/upload"
                className="mt-3 inline-flex rounded-lg border border-[#d7d3c8] bg-white px-3 py-2 text-xs"
              >
                Yukleme ekranina git
              </Link>
            </div>
          ) : (
            items.map((f) => (
              <div
                key={f.file_id}
                className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[#e3dfd3] bg-[#f7f5ef] px-4 py-3"
              >
                <div>
                  <div className="text-sm font-semibold text-[#0c2a2a]">{f.original_filename}</div>
                  <div className="text-xs text-[#4f6f6b]">{statusLabel[f.status] || f.status}</div>
                </div>
                <div className="flex items-center gap-2 text-xs">
                  {f.status === "ready" ? (
                    <Link
                      href={`/view/${f.file_id}`}
                      className="rounded-lg border border-[#d7d3c8] bg-white px-3 py-1 text-[#2c4b49]"
                    >
                      Goruntule
                    </Link>
                  ) : null}
                </div>
              </div>
            ))
          )}
        </div>
      </section>

      <section className="mt-6 rounded-2xl border border-[#d7d3c8] bg-white/80 p-5">
        <div className="text-sm font-semibold text-[#0c2a2a]">Paylasimlar</div>
        <div className="mt-4 text-center text-sm text-[#2c4b49]">
          <div className="text-2xl">⭘</div>
          <div className="mt-2">Paylasim kaydi yok. Bir dosyayi view ekranindan paylas.</div>
          <Link
            href="/upload"
            className="mt-3 inline-flex rounded-lg border border-[#d7d3c8] bg-white px-3 py-2 text-xs"
          >
            Dosya yukle
          </Link>
        </div>
      </section>
    </main>
  );
}
