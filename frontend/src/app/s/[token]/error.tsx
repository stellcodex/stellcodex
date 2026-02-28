"use client";

import Link from "next/link";

export default function ShareTokenError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="grid min-h-screen place-items-center bg-[#0b1220] px-4 text-white">
      <div className="w-full max-w-md rounded-2xl border border-[#334155] bg-[#0f172a] p-6">
        <div className="text-lg font-semibold text-[#fda4af]">Share Error</div>
        <p className="mt-2 text-sm text-[#cbd5e1]">Paylaşım görüntülenirken beklenmeyen bir hata oluştu.</p>
        <p className="mt-2 rounded border border-[#1f2937] bg-[#020617] px-2 py-1 text-xs text-[#94a3b8]">
          {error.message || "unknown error"}
        </p>
        <div className="mt-4 flex items-center gap-2">
          <button
            type="button"
            onClick={reset}
            className="rounded-lg border border-[#334155] bg-[#111827] px-3 py-2 text-xs font-semibold text-white hover:bg-[#1f2937]"
          >
            Tekrar Dene
          </button>
          <Link href="/" className="rounded-lg border border-[#334155] bg-[#111827] px-3 py-2 text-xs font-semibold text-white hover:bg-[#1f2937]">
            Ana Sayfa
          </Link>
        </div>
      </div>
    </main>
  );
}

