"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import logo from "@/app/gorsel/logo.png";
import { UploadDrop } from "@/components/upload/UploadDrop";
import { listFiles, type FileItem } from "@/services/api";

export default function HomePage() {
  const router = useRouter();
  const [leftOpen, setLeftOpen] = useState(false);
  const [recent, setRecent] = useState<FileItem[]>([]);
  const [loadingRecent, setLoadingRecent] = useState(true);
  const [recentError, setRecentError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const files = await listFiles();
        if (!alive) return;
        setRecent(files.slice(0, 8));
      } catch (error) {
        if (!alive) return;
        setRecentError(error instanceof Error ? error.message : "Dosya listesi alınamadı.");
      } finally {
        if (alive) setLoadingRecent(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  return (
    <div className="h-[100dvh] overflow-hidden bg-[#f7f7f8] text-[#111827]">
      <header className="sticky top-0 z-30 border-b border-[#e5e7eb] bg-white">
        <div className="mx-auto flex h-16 max-w-[1440px] items-center justify-between gap-3 px-3 sm:px-4">
          <div className="flex items-center gap-2">
            <button
              type="button"
              className="grid h-9 w-9 place-items-center rounded-lg border border-[#d1d5db] bg-white text-sm text-[#111827] md:hidden"
              onClick={() => setLeftOpen(true)}
              aria-label="Sidebar aç"
            >
              ☰
            </button>
            <Link href="/" className="flex items-center gap-2">
              <Image src={logo} alt="STELLCODEX logo" width={34} height={34} className="h-8 w-8 rounded-md object-cover" />
              <span className="hidden text-sm font-semibold tracking-wide text-[#111827] sm:inline">STELLCODEX</span>
            </Link>
          </div>
          <div className="flex items-center gap-2">
            <Link href="/upload" className="rounded-lg border border-[#111827] bg-[#111827] px-3 py-2 text-xs font-semibold text-white">
              Dosya Yükle
            </Link>
          </div>
        </div>
      </header>

      <div className="mx-auto flex h-[calc(100dvh-4rem)] max-w-[1440px] overflow-hidden">
        <aside className="hidden w-[280px] shrink-0 border-r border-[#e5e7eb] bg-white md:flex md:flex-col">
          <div className="p-4">
            <div className="text-xs font-semibold uppercase tracking-[0.16em] text-[#6b7280]">Library</div>
            <div className="mt-2 rounded-lg border border-[#e5e7eb] bg-[#f9fafb] p-3 text-xs text-[#6b7280]">
              Placeholder: projeler, klasörler ve koleksiyonlar.
            </div>
          </div>
          <div className="border-t border-[#e5e7eb] p-4">
            <div className="text-xs font-semibold uppercase tracking-[0.16em] text-[#6b7280]">History</div>
            <div className="mt-2 rounded-lg border border-[#e5e7eb] bg-[#f9fafb] p-3 text-xs text-[#6b7280]">
              Son konuşmalar ve yükleme geçmişi burada görünecek.
            </div>
          </div>
        </aside>

        <main className="min-w-0 flex-1 overflow-y-auto">
          <div className="mx-auto flex min-h-full w-full max-w-4xl flex-col px-3 py-4 sm:px-5 sm:py-6">
            <section className="rounded-2xl border border-[#e5e7eb] bg-white p-4 sm:p-6">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#6b7280]">Composite Workspace</p>
              <h1 className="mt-3 text-xl font-semibold tracking-tight text-[#111827] sm:text-2xl">
                Dosyanı yükle, işleyelim ve doğrudan viewer&apos;a geçelim.
              </h1>
              <p className="mt-2 text-sm text-[#4b5563]">
                Drag &amp; drop veya dosya seçimi ile yükleme başlar. Durum hazır olduğunda otomatik olarak{" "}
                <code className="rounded bg-[#f3f4f6] px-1 py-0.5 text-xs text-[#111827]">/view/{"{scx_id}"}</code>{" "}
                sayfasına yönlendirilirsin.
              </p>
              <div className="mt-5">
                <UploadDrop
                  onUploaded={(fileId) => {
                    router.push(`/view/${fileId}`);
                  }}
                />
              </div>
            </section>

            <section className="mt-4 rounded-2xl border border-[#e5e7eb] bg-white p-4 sm:p-6">
              <div className="flex items-center justify-between gap-3">
                <h2 className="text-sm font-semibold text-[#111827]">Son Yüklenen Dosyalar</h2>
                <Link href="/files" className="text-xs font-semibold text-[#374151] hover:text-[#111827]">
                  Tümünü aç
                </Link>
              </div>
              {loadingRecent ? (
                <div className="mt-3 text-sm text-[#6b7280]">Yükleniyor...</div>
              ) : recentError ? (
                <div className="mt-3 text-sm text-red-600">{recentError}</div>
              ) : recent.length === 0 ? (
                <div className="mt-3 text-sm text-[#6b7280]">Henüz yükleme yok.</div>
              ) : (
                <div className="mt-3 grid gap-2">
                  {recent.map((file) => (
                    <Link
                      key={file.file_id}
                      href={`/view/${file.file_id}`}
                      className="flex items-center justify-between rounded-lg border border-[#e5e7eb] bg-[#f9fafb] px-3 py-2 text-sm text-[#374151] hover:bg-white"
                    >
                      <span className="truncate pr-3">{file.original_filename}</span>
                      <span className="shrink-0 text-xs uppercase tracking-[0.08em] text-[#6b7280]">{file.status}</span>
                    </Link>
                  ))}
                </div>
              )}
            </section>
          </div>
        </main>

        <aside className="hidden w-[280px] shrink-0 border-l border-[#e5e7eb] bg-white xl:block">
          <div className="p-4">
            <h2 className="text-xs font-semibold uppercase tracking-[0.16em] text-[#6b7280]">Tips</h2>
            <ul className="mt-3 grid gap-2 text-xs text-[#4b5563]">
              <li className="rounded-lg border border-[#e5e7eb] bg-[#f9fafb] px-3 py-2">Upload sonrası status otomatik izlenir.</li>
              <li className="rounded-lg border border-[#e5e7eb] bg-[#f9fafb] px-3 py-2">Viewer parça sayısı manifest üzerinden gösterilir.</li>
              <li className="rounded-lg border border-[#e5e7eb] bg-[#f9fafb] px-3 py-2">Share linkleri read-only public view açar.</li>
            </ul>
          </div>
        </aside>
      </div>

      {leftOpen ? (
        <div className="fixed inset-0 z-50 md:hidden">
          <button
            type="button"
            className="absolute inset-0 bg-black/35"
            aria-label="Sidebar kapat"
            onClick={() => setLeftOpen(false)}
          />
          <aside className="absolute left-0 top-0 h-full w-[84vw] max-w-[320px] overflow-y-auto border-r border-[#e5e7eb] bg-white p-4 shadow-xl">
            <div className="flex items-center justify-between">
              <div className="text-xs font-semibold uppercase tracking-[0.16em] text-[#6b7280]">Menu</div>
              <button
                type="button"
                className="rounded-lg border border-[#d1d5db] px-2 py-1 text-xs"
                onClick={() => setLeftOpen(false)}
              >
                Kapat
              </button>
            </div>
            <div className="mt-4 grid gap-2">
              <Link href="/files" className="rounded-lg border border-[#e5e7eb] bg-[#f9fafb] px-3 py-2 text-sm text-[#374151]" onClick={() => setLeftOpen(false)}>
                Library
              </Link>
              <Link href="/dashboard" className="rounded-lg border border-[#e5e7eb] bg-[#f9fafb] px-3 py-2 text-sm text-[#374151]" onClick={() => setLeftOpen(false)}>
                History
              </Link>
            </div>
          </aside>
        </div>
      ) : null}
    </div>
  );
}
