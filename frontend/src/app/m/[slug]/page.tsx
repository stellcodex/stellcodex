import type { Metadata } from "next";
import Link from "next/link";
import { headers } from "next/headers";
import { notFound } from "next/navigation";

export const dynamic = "force-dynamic";
export const revalidate = 0;

type PublicLibraryItem = {
  slug: string;
  title: string;
  description?: string | null;
  tags?: string[];
  cover_thumb?: string | null;
  share_url?: string | null;
};

async function getOrigin() {
  const reqHeaders = await headers();
  const proto = reqHeaders.get("x-forwarded-proto") || "http";
  const host = reqHeaders.get("x-forwarded-host") || reqHeaders.get("host") || "127.0.0.1:3010";
  return `${proto}://${host}`;
}

function normalizeApiPath(pathname: string) {
  const basePath = pathname.replace(/\/+$/, "");
  if (!basePath || basePath === "/") return "/api/v1";
  if (basePath === "/api") return "/api/v1";
  if (basePath === "/api/v1" || basePath.endsWith("/api/v1")) return basePath;
  if (basePath.endsWith("/api")) return `${basePath}/v1`;
  return `${basePath}/api/v1`;
}

async function resolveApiBase() {
  const origin = await getOrigin();
  const raw = (process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_API_BASE || "/api/v1").trim();
  if (/^https?:\/\//i.test(raw)) {
    try {
      const parsed = new URL(raw);
      return `${parsed.origin}${normalizeApiPath(parsed.pathname)}`;
    } catch {
      return `${origin}/api/v1`;
    }
  }
  if (raw.startsWith("/")) return `${origin}${normalizeApiPath(raw)}`;
  return `${origin}${normalizeApiPath(`/${raw}`)}`;
}

async function fetchItem(slug: string): Promise<PublicLibraryItem | null> {
  const apiBase = await resolveApiBase();
  const res = await fetch(`${apiBase}/library/item/${encodeURIComponent(slug)}`, {
    cache: "no-store",
    next: { revalidate: 0 },
  });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`library item failed: ${res.status}`);
  return res.json();
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params;
  const item = await fetchItem(slug).catch(() => null);
  if (!item) {
    return { title: "Library Item | STELLCODEX" };
  }
  return {
    title: `${item.title} | STELLCODEX`,
    description: item.description || "Public model page",
    openGraph: {
      title: item.title,
      description: item.description || "Public model page",
      images: item.cover_thumb ? [item.cover_thumb] : [],
    },
  };
}

export default async function PublicModelPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const item = await fetchItem(slug);
  if (!item) notFound();

  return (
    <main className="mx-auto max-w-6xl space-y-4 px-4 py-4">
      <header className="rounded-2xl border border-slate-200 bg-white p-4">
        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Public Model</div>
        <h1 className="mt-1 text-xl font-semibold text-slate-900">{item.title}</h1>
        <p className="mt-1 text-sm text-slate-600">{item.description || "Açıklama yok."}</p>
      </header>

      <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
        {item.share_url ? (
          <iframe title={item.title} src={item.share_url} className="h-[78vh] w-full" />
        ) : (
          <div className="p-4 text-sm text-slate-500">Bu model için share viewer bulunamadı.</div>
        )}
      </section>

      <footer className="flex items-center gap-2">
        <Link href="/library" className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700">
          Library Feed
        </Link>
        {item.share_url ? (
          <Link href={item.share_url} className="rounded-lg border border-slate-300 bg-slate-50 px-3 py-1.5 text-xs font-semibold text-slate-700">
            Share Link
          </Link>
        ) : null}
      </footer>
    </main>
  );
}
