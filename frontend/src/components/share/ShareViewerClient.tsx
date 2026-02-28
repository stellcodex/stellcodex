"use client";

import { useMemo, useRef, useState } from "react";
import Link from "next/link";
import { ThreeViewer } from "@/components/viewer/ThreeViewer";

type ShareViewerPolicy = {
  permission: string;
  canView: boolean;
  canDownload: boolean;
  expiresAt: string;
  contentType: string;
  originalFilename: string;
  gltfUrl: string | null;
  originalUrl: string | null;
};

type ShareViewerClientProps = {
  fileId: string;
  shareToken: string;
  policy: ShareViewerPolicy;
};

function formatTimestamp() {
  const now = new Date();
  const pad = (value: number) => String(value).padStart(2, "0");
  return `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}_${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`;
}

export function ShareViewerClient({ fileId, shareToken, policy }: ShareViewerClientProps) {
  const [state] = useState(() => ({ fileId, shareToken, policy }));
  const hostRef = useRef<HTMLDivElement | null>(null);
  const canExport = state.policy.canDownload;

  const subtitle = useMemo(() => {
    if (state.policy.permission === "download") return "Read-only + download";
    if (state.policy.permission === "comment") return "Read-only + comment";
    return "Read-only";
  }, [state.policy.permission]);

  const exportPng = () => {
    if (!canExport) return;
    const canvas = hostRef.current?.querySelector("canvas");
    if (!canvas) return;
    canvas.toBlob((blob) => {
      if (!blob) return;
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `stellcodex_${state.fileId}_${formatTimestamp()}.png`;
      anchor.click();
      URL.revokeObjectURL(url);
    }, "image/png");
  };

  const renderSurface = () => {
    if (!state.policy.canView) {
      return <div className="p-4 text-sm text-[#6b7280]">Bu paylaşım için görüntüleme izni yok.</div>;
    }
    if (state.policy.gltfUrl) {
      return (
        <div ref={hostRef} className="h-full">
          <ThreeViewer url={state.policy.gltfUrl} />
        </div>
      );
    }
    if (!state.policy.originalUrl) {
      return <div className="p-4 text-sm text-[#6b7280]">İçerik hazır değil.</div>;
    }
    if (state.policy.contentType === "application/pdf") {
      return <iframe title="Shared PDF" src={state.policy.originalUrl} className="h-full w-full rounded-xl" />;
    }
    if (state.policy.contentType.startsWith("image/")) {
      return <img src={state.policy.originalUrl} alt={state.policy.originalFilename} className="h-full w-full object-contain" />;
    }
    return <div className="p-4 text-sm text-[#6b7280]">Bu içerik türü share viewer içinde önizlenemiyor.</div>;
  };

  return (
    <main className="h-full overflow-hidden bg-[#0b1220] text-[#e5e7eb]">
      <div className="mx-auto flex h-full max-w-[1600px] flex-col gap-3 px-3 py-3 sm:px-6 sm:py-5">
        <header className="flex items-center justify-between rounded-xl border border-[#1f2937] bg-[#0f172a] px-3 py-2">
          <div className="min-w-0">
            <div className="truncate text-sm font-semibold">File ID: {state.fileId}</div>
            <div className="text-xs text-[#93c5fd]">{subtitle}</div>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={exportPng}
              disabled={!canExport}
              className={`rounded-md border px-3 py-1.5 text-xs font-semibold ${
                canExport ? "border-[#334155] bg-[#111827] text-white hover:bg-[#1f2937]" : "cursor-not-allowed border-[#1f2937] bg-[#0f172a] text-[#64748b]"
              }`}
              title={canExport ? "PNG dışa aktar" : "Bu paylaşımda indirme kapalı"}
            >
              Export PNG
            </button>
            <Link href="/" className="rounded-md border border-[#334155] bg-[#111827] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#1f2937]">
              Ana Sayfa
            </Link>
          </div>
        </header>

        <section className="min-h-0 flex-1 overflow-hidden rounded-2xl border border-[#1f2937] bg-[#020617]">{renderSurface()}</section>
      </div>
    </main>
  );
}

