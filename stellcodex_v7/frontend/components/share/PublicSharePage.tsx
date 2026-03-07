"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/common/Button";
import { getPublicShare } from "@/lib/api";

export function PublicSharePage({ token }: { token: string }) {
  const [data, setData] = useState<Awaited<ReturnType<typeof getPublicShare>> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const result = await getPublicShare(token);
        if (alive) setData(result);
      } catch (e) {
        if (alive) setError(e instanceof Error ? e.message : "Paylaşım yüklenemedi.");
      }
    })();
    return () => {
      alive = false;
    };
  }, [token]);

  if (error) return <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>;
  if (!data) return <div className="rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-600">Yükleniyor...</div>;

  return (
    <div className="mx-auto max-w-3xl p-4 sm:p-8">
      <div className="rounded-2xl border border-slate-200 bg-white p-5">
        <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">STELLCODEX Share</div>
        <h1 className="mt-2 text-xl font-semibold text-slate-900">{data.file.name}</h1>
        <p className="mt-1 text-sm text-slate-600">
          {data.file.kind} · {data.file.engine}
        </p>
        {data.expiresAt ? (
          <p className="mt-2 rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-700">Süre sonu: {data.expiresAt}</p>
        ) : (
          <p className="mt-2 text-sm text-slate-500">Süre sınırı belirtilmedi.</p>
        )}

        <div className="mt-4 grid min-h-[260px] place-items-center rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-6 text-center">
          {data.canView ? (
            <div>
              <div className="text-sm font-medium text-slate-800">Public preview placeholder</div>
              <div className="mt-1 text-sm text-slate-500">Dosya önizleme bu alanda gösterilir.</div>
            </div>
          ) : (
            <div className="text-sm text-slate-500">Bu linkte görüntüleme izni yok.</div>
          )}
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          {data.canDownload ? (
            <Button href={data.downloadUrl} variant="primary">
              İndir
            </Button>
          ) : (
            <button
              disabled
              className="h-10 rounded-xl border border-slate-200 px-4 text-sm text-slate-400"
            >
              İndirme izni yok
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

