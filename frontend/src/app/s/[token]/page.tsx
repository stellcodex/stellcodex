import Link from "next/link";
import { headers } from "next/headers";
import { notFound } from "next/navigation";
import { ShareViewerClient } from "@/components/share/ShareViewerClient";

export const dynamic = "force-dynamic";
export const revalidate = 0;

type ShareResolvePayload = {
  file_id: string;
  permission: string;
  can_view: boolean;
  can_download: boolean;
  expires_at: string;
  content_type: string;
  original_filename: string;
  gltf_url?: string | null;
  original_url?: string | null;
};

type SharePolicy = {
  permission: string;
  canView: boolean;
  canDownload: boolean;
  expiresAt: string;
  contentType: string;
  originalFilename: string;
  gltfUrl: string | null;
  originalUrl: string | null;
};

function normalizeApiPath(pathname: string) {
  const basePath = pathname.replace(/\/+$/, "");
  if (!basePath || basePath === "/") return "/api/v1";
  if (basePath === "/api") return "/api/v1";
  if (basePath === "/api/v1" || basePath.endsWith("/api/v1")) return basePath;
  if (basePath.endsWith("/api")) return `${basePath}/v1`;
  return `${basePath}/api/v1`;
}

async function getRequestOrigin() {
  const reqHeaders = await headers();
  const proto = reqHeaders.get("x-forwarded-proto") || "http";
  const host = reqHeaders.get("x-forwarded-host") || reqHeaders.get("host") || "127.0.0.1:3010";
  return `${proto}://${host}`;
}

async function resolveApiBase() {
  const raw = (process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_API_BASE || "/api/v1").trim();
  const origin = await getRequestOrigin();

  if (/^https?:\/\//i.test(raw)) {
    try {
      const parsed = new URL(raw);
      return `${parsed.origin}${normalizeApiPath(parsed.pathname)}`;
    } catch {
      return `${origin}/api/v1`;
    }
  }

  if (raw.startsWith("/")) {
    return `${origin}${normalizeApiPath(raw)}`;
  }
  return `${origin}${normalizeApiPath(`/${raw}`)}`;
}

async function fetchShareResolve(token: string): Promise<{ fileId: string; policy: SharePolicy } | { status: "expired" } | { status: "not_found" }> {
  const apiBase = await resolveApiBase();
  const res = await fetch(`${apiBase}/share/resolve?share_token=${encodeURIComponent(token)}`, {
    method: "GET",
    cache: "no-store",
    next: { revalidate: 0 },
  });

  if (res.status === 410) return { status: "expired" };
  if (res.status === 404 || res.status === 401) return { status: "not_found" };
  if (!res.ok) {
    throw new Error(`share resolve failed: ${res.status}`);
  }

  const data = (await res.json().catch(() => null)) as ShareResolvePayload | null;
  if (!data || typeof data.file_id !== "string" || data.file_id.trim().length === 0) {
    throw new Error("share resolve payload invalid");
  }

  return {
    fileId: data.file_id,
    policy: {
      permission: typeof data.permission === "string" ? data.permission : "view",
      canView: Boolean(data.can_view),
      canDownload: Boolean(data.can_download),
      expiresAt: typeof data.expires_at === "string" ? data.expires_at : "",
      contentType: typeof data.content_type === "string" ? data.content_type : "application/octet-stream",
      originalFilename: typeof data.original_filename === "string" ? data.original_filename : data.file_id,
      gltfUrl: typeof data.gltf_url === "string" ? data.gltf_url : null,
      originalUrl: typeof data.original_url === "string" ? data.original_url : null,
    },
  };
}

export default async function ShareTokenPage({ params }: { params: Promise<{ token: string }> }) {
  const { token } = await params;
  const resolved = await fetchShareResolve(token);

  if ("status" in resolved) {
    if (resolved.status === "not_found") {
      notFound();
    }
    return (
      <main className="grid min-h-screen place-items-center bg-[#0b1220] px-4 text-white">
        <div className="w-full max-w-md rounded-2xl border border-[#334155] bg-[#0f172a] p-6">
          <div className="text-lg font-semibold text-[#fda4af]">410 Link Expired</div>
          <p className="mt-2 text-sm text-[#cbd5e1]">Bu paylaşım bağlantısının süresi dolmuş.</p>
          <Link href="/" className="mt-4 inline-flex rounded-lg border border-[#334155] bg-[#111827] px-3 py-2 text-xs font-semibold text-white hover:bg-[#1f2937]">
            Ana Sayfaya Dön
          </Link>
        </div>
      </main>
    );
  }

  return <ShareViewerClient fileId={resolved.fileId} shareToken={token} policy={resolved.policy} />;
}
