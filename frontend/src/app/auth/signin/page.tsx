import Link from "next/link";

function providers() {
  const items = [];
  if (process.env.GOOGLE_CLIENT_ID && process.env.GOOGLE_CLIENT_SECRET) {
    items.push({ id: "google", label: "Google" });
  }
  if (process.env.APPLE_CLIENT_ID && process.env.APPLE_CLIENT_SECRET) {
    items.push({ id: "apple", label: "Apple" });
  }
  if (process.env.FACEBOOK_CLIENT_ID && process.env.FACEBOOK_CLIENT_SECRET) {
    items.push({ id: "facebook", label: "Facebook" });
  }
  return items;
}

export default function AuthSignInPage() {
  const authProviders = providers();
  return (
    <main className="mx-auto max-w-xl px-6 py-8">
      <section className="rounded-3xl border border-slate-200 bg-white p-6">
        <h1 className="text-xl font-semibold text-slate-900">Sign in</h1>
        <p className="mt-2 text-sm text-slate-600">Google, Apple veya Facebook ile devam et.</p>
        <div className="mt-4 grid gap-2">
          {authProviders.map((provider) => (
            <Link
              key={provider.id}
              href={`/api/auth/signin/${provider.id}`}
              className="inline-flex h-10 items-center justify-center rounded-xl border border-slate-300 bg-white text-sm font-semibold text-slate-700"
            >
              {provider.label} ile giriş
            </Link>
          ))}
          <Link href="/dashboard" className="inline-flex h-10 items-center justify-center rounded-xl border border-slate-300 bg-slate-50 text-sm font-semibold text-slate-700">
            Misafir session
          </Link>
        </div>
      </section>
    </main>
  );
}

