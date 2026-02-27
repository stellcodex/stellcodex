"use client";

import { useEffect, useState, type ReactNode } from "react";
import Image from "next/image";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ThreeViewer } from "@/components/viewer/ThreeViewer";
import logo from "@/app/gorsel/logo.png";
import { resolveShare } from "@/services/api";

export default function SharePage() {
  const params = useParams<{ token: string }>();
  const token = params?.token;

  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    resolveShare(token)
      .then(setData)
      .catch((e) => setError(e?.message || "Paylaşım yüklenemedi."));
  }, [token]);

  let content: ReactNode;

  if (error) {
    const lower = error.toLowerCase();
    const expired = lower.includes("expired");
    const invalid = lower.includes("invalid");
    content = (
      <div className="rounded-2xl border border-[#fecaca] bg-[#fff1f2] p-5">
        <div className="text-sm font-semibold text-[#b91c1c]">{expired ? "Link expired" : invalid ? "Geçersiz paylaşım linki" : "Paylaşım açılamadı"}</div>
        <div className="mt-2 text-sm text-[#7f1d1d]">{error}</div>
        <Link href="/" className="mt-4 inline-flex rounded-lg border border-[#fca5a5] bg-white px-3 py-2 text-xs font-semibold text-[#7f1d1d]">
          Ana sayfaya dön
        </Link>
      </div>
    );
  } else if (!data) {
    content = <div className="rounded-xl border border-[#e5e7eb] bg-white p-4 text-sm text-[#6b7280]">Shared view yükleniyor...</div>;
  } else {
    content = (
      <>
        <div className="mb-4 flex items-center justify-between gap-3 rounded-xl border border-[#e5e7eb] bg-white px-4 py-3">
          <div className="min-w-0">
            <div className="truncate text-sm font-semibold text-[#111827]">{data.original_filename}</div>
            <div className="text-xs text-[#6b7280]">Read-only shared view</div>
          </div>
          <Link href="/" className="shrink-0 rounded-lg border border-[#d1d5db] bg-white px-3 py-2 text-xs font-semibold text-[#374151]">
            Ana sayfa
          </Link>
        </div>

        <div className="h-[min(78vh,calc(100dvh-12rem))] overflow-hidden rounded-2xl border border-[#e5e7eb] bg-white">
          {data.gltf_url ? (
            <ThreeViewer
              url={data.gltf_url}
              renderMode="shadedEdges"
              clip={false}
              clipOffset={0}
            />
          ) : data.original_url ? (
            data.content_type === "application/pdf" ? (
              <iframe
                title="Paylaşılan içerik"
                src={data.original_url}
                className="h-full w-full rounded-3xl"
              />
            ) : (
              <img
                src={data.original_url}
                className="h-full w-full object-contain"
                alt="önizleme"
              />
            )
          ) : (
            <div className="p-4 text-sm text-slate-500">İçerik hazır değil.</div>
          )}
        </div>
      </>
    );
  }

  return (
    <main className="h-full overflow-hidden bg-[#f7f7f8]">
      <div className="mx-auto flex h-full max-w-6xl flex-col gap-4 px-3 py-3 sm:px-6 sm:py-4">
        <header className="flex items-center justify-between rounded-xl border border-[#e5e7eb] bg-white px-3 py-2">
          <div className="flex items-center gap-2">
            <Image src={logo} alt="STELLCODEX logo" width={30} height={30} className="h-7 w-7 rounded-md object-cover" />
            <div className="hidden text-sm font-semibold text-[#111827] sm:block">Shared View</div>
          </div>
          <div className="text-xs text-[#6b7280]">Token: {token}</div>
        </header>
        <div className="min-h-0 flex-1 overflow-y-auto">{content}</div>
      </div>
    </main>
  );
}
