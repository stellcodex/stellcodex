import Link from "next/link";
import { Button } from "@/components/ui/Button";

function providers() {
  const items = [];
  if (process.env.GOOGLE_CLIENT_ID && process.env.GOOGLE_CLIENT_SECRET) {
    items.push({ id: "google", label: "Google ile giriş" });
  }
  if (process.env.APPLE_CLIENT_ID && process.env.APPLE_CLIENT_SECRET) {
    items.push({ id: "apple", label: "Apple ile giriş" });
  }
  if (process.env.FACEBOOK_CLIENT_ID && process.env.FACEBOOK_CLIENT_SECRET) {
    items.push({ id: "facebook", label: "Facebook ile giriş" });
  }
  return items;
}

export default function LoginPage() {
  const authProviders = providers();

  return (
    <main className="mx-auto max-w-4xl px-6 py-6 sm:py-8">
      <section className="rounded-3xl border border-[#d7d3c8] bg-white/80 p-5 shadow-sm">
        <div className="text-xs font-semibold uppercase tracking-[0.2em] text-[#4f6f6b]">Sign In</div>
        <h1 className="mt-3 text-xl font-semibold text-[#0c2a2a] sm:text-2xl">Stellcodex hesabına giriş yap</h1>
        <p className="mt-3 text-sm text-[#2c4b49]">Tek bir oturumla dashboard, viewer ve paylaşım yönetimini kullan.</p>

        <div className="mt-6 flex flex-wrap gap-3">
          {authProviders.map((provider) => (
            <Link
              key={provider.id}
              href={`/api/auth/signin/${provider.id}`}
              className="inline-flex h-10 items-center rounded-xl border border-[#d7d3c8] bg-white px-4 text-sm font-semibold text-[#1f2937]"
            >
              {provider.label}
            </Link>
          ))}
          <Button href="/dashboard" variant="secondary">
            Misafir oturumu
          </Button>
        </div>

        {authProviders.length === 0 ? (
          <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
            OAuth provider konfigürasyonu bulunamadı. Misafir oturumu ile devam edebilirsin.
          </div>
        ) : null}
      </section>
    </main>
  );
}

