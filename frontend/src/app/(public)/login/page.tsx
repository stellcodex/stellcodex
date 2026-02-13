import Link from "next/link";
import { LoginButton } from "@/components/auth/LoginButton";
import { Button } from "@/components/ui/Button";

export default function LoginPage() {
  return (
    <main className="mx-auto max-w-4xl px-6 py-6 sm:py-8">
      <section className="rounded-3xl border border-[#d7d3c8] bg-white/80 p-5 shadow-sm">
        <div className="text-xs font-semibold uppercase tracking-[0.2em] text-[#4f6f6b]">Giriş</div>
        <h1 className="mt-3 text-xl font-semibold text-[#0c2a2a] sm:text-2xl">
          Stellcodex hesabına giriş yap
        </h1>
        <p className="mt-3 text-sm text-[#2c4b49]">
          Google veya LinkedIn ile güvenli giriş. OAuth aktif değilse misafir moduyla devam edebilirsin.
        </p>

        <div className="mt-6 flex flex-wrap gap-3">
          <LoginButton />
          <Button href="/files" variant="secondary">
            Misafir olarak devam et
          </Button>
        </div>

        <div className="mt-8 rounded-2xl border border-[#e3dfd3] bg-[#f7f5ef] p-4 text-sm text-[#2c4b49]">
          <div className="font-semibold text-[#0c2a2a]">Neler açılır?</div>
          <ul className="mt-2 grid gap-2">
            <li>Panel ve dosya durumları</li>
            <li>Paylaşım linkleri ve geçmiş</li>
            <li>Takım için ek kontroller</li>
          </ul>
        </div>

        <div className="mt-8 text-xs text-[#4f6f6b]">
          Hesap sorunları için{" "}
          <Link className="underline" href="/docs">
            Dokümanlar
          </Link>{" "}
          sayfasına git.
        </div>
      </section>
    </main>
  );
}
