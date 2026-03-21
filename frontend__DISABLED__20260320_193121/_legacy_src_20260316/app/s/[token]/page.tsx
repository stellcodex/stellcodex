"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ApiHttpError, resolveShare, ShareResolveResult } from "@/services/api";
import { ShareViewerClient } from "@/components/share/ShareViewerClient";

type SharePageError = {
  status: number;
  title: string;
  description: string;
};

function classifyShareError(error: unknown): SharePageError {
  if (error instanceof ApiHttpError) {
    if (error.status === 403) {
      return { status: 403, title: "Access disabled", description: error.message || "This share link has been revoked or access was disabled." };
    }
    if (error.status === 404) {
      return { status: 404, title: "Link not found", description: "The share link is invalid or was removed." };
    }
    if (error.status === 410) {
      return { status: 410, title: "Link expired", description: error.message || "This share link has expired." };
    }
    if (error.status === 429) {
      return { status: 429, title: "Too many requests", description: error.message || "Try again in a moment." };
    }
    return { status: error.status, title: "Share could not be loaded", description: error.message || "Unexpected error." };
  }
  if (error instanceof Error) {
    return { status: 500, title: "Share could not be loaded", description: error.message };
  }
  return { status: 500, title: "Share could not be loaded", description: "Unexpected error." };
}

export default function PublicShareRoute({ params }: { params: { token: string } }) {
  const token = typeof params?.token === "string" ? params.token : "";
  const [data, setData] = useState<ShareResolveResult | null>(null);
  const [error, setError] = useState<SharePageError | null>(null);

  useEffect(() => {
    let active = true;
    if (!token) {
      setError({ status: 404, title: "Link not found", description: "The share link is invalid." });
      return () => {
        active = false;
      };
    }
    (async () => {
      try {
        const result = await resolveShare(token);
        if (!active) return;
        setData(result);
        setError(null);
      } catch (err) {
        if (!active) return;
        setData(null);
        setError(classifyShareError(err));
      }
    })();
    return () => {
      active = false;
    };
  }, [token]);

  if (error) {
    return (
      <main className="grid min-h-screen place-items-center bg-[#0b1220] px-4 text-[#e2e8f0]">
        <div className="w-full max-w-xl rounded-3xl border border-[#334155] bg-[#0f172a] p-6 shadow-[0_24px_60px_rgba(2,6,23,0.5)]">
          <div className="text-sm font-semibold uppercase tracking-[0.18em] text-[#93c5fd]">STELLCODEX Share</div>
          <h1 className="mt-3 text-2xl font-semibold text-white">{error.title}</h1>
          <p className="mt-2 text-sm text-[#cbd5e1]">{error.description}</p>
          <div className="mt-4 inline-flex rounded-full border border-[#334155] bg-[#111827] px-3 py-1 text-xs text-[#93c5fd]">
            HTTP {error.status}
          </div>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link href="/" className="rounded-xl border border-[#334155] bg-[#111827] px-4 py-2 text-sm font-semibold text-white hover:bg-[#1f2937]">
              Home
            </Link>
          </div>
        </div>
      </main>
    );
  }

  if (!data) {
    return (
      <main className="grid min-h-screen place-items-center bg-[#0b1220] px-4 text-[#e2e8f0]">
        <div className="w-full max-w-xl rounded-3xl border border-[#334155] bg-[#0f172a] p-6">
          <div className="text-sm font-semibold uppercase tracking-[0.18em] text-[#93c5fd]">STELLCODEX Share</div>
          <div className="mt-4 h-3 w-40 animate-pulse rounded-full bg-[#1e293b]" />
          <div className="mt-3 h-3 w-full animate-pulse rounded-full bg-[#1e293b]" />
          <div className="mt-2 h-3 w-5/6 animate-pulse rounded-full bg-[#1e293b]" />
        </div>
      </main>
    );
  }

  return (
    <ShareViewerClient
      fileId={data.file_id}
      shareToken={token}
      policy={{
        permission: data.permission,
        canView: data.can_view,
        canDownload: data.can_download,
        expiresAt: data.expires_at,
        contentType: data.content_type,
        originalFilename: data.original_filename,
        gltfUrl: data.gltf_url || null,
        originalUrl: data.original_url || null,
      }}
    />
  );
}
