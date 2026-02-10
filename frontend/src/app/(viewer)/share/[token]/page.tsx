"use client";

import { useEffect, useState, type ReactNode } from "react";
import { useParams } from "next/navigation";
import { ThreeViewer } from "@/components/viewer/ThreeViewer";
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
      .catch((e) => setError(e?.message || "Paylasim yuklenemedi."));
  }, [token]);

  let content: ReactNode;

  if (error) {
    content = <div className="text-sm text-red-600">{error}</div>;
  } else if (!data) {
    content = <div className="text-sm text-slate-500">Yukleniyor...</div>;
  } else {
    content = (
      <>
        <div className="mb-4 text-sm font-semibold text-slate-900">
          {data.original_filename}
        </div>

        <div className="h-[75vh] overflow-hidden rounded-3xl border border-slate-200 bg-white">
          {data.gltf_url ? (
            <ThreeViewer
              url={data.gltf_url}
              renderMode="shaded"
              clip={false}
              clipOffset={0}
            />
          ) : data.original_url ? (
            data.content_type === "application/pdf" ? (
              <iframe
                title="Paylasilan icerik"
                src={data.original_url}
                className="h-full w-full rounded-3xl"
              />
            ) : (
              <img
                src={data.original_url}
                className="h-full w-full object-contain"
                alt="preview"
              />
            )
          ) : (
            <div className="p-4 text-sm text-slate-500">Icerik hazir degil.</div>
          )}
        </div>
      </>
    );
  }

  return <main className="mx-auto max-w-6xl px-6 py-10">{content}</main>;
}
