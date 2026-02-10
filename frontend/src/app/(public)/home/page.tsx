import Image from "next/image";
import Link from "next/link";
import { Button } from "@/components/ui/Button";

export default function HomePage() {
  return (
    <main className="mx-auto max-w-6xl px-6 pb-16 pt-14">
      <section className="grid gap-10 lg:grid-cols-[1.15fr_0.85fr]">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full border border-[#d7d3c8] bg-[#f7f5ef] px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-[#4f6f6b]">
            STELLCODEX ENGINEERING VIEWER
          </div>
          <h1 className="mt-4 text-4xl font-semibold tracking-tight text-[#0c2a2a] sm:text-5xl">
            Visualize. Review. Share. Engineering data — without CAD.
          </h1>
          <p className="mt-4 max-w-xl text-sm text-[#2c4b49] sm:text-base">
            Endustriyel tasarimcilar, imalat ekipleri ve CAD lisansi olmayan karar
            vericiler icin. Dosyayi yukle, 2D/3D goruntule, link ile paylas.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Button href="/upload">Dosya Yukle</Button>
            <Button href="/community" variant="secondary">
              Library / Community
            </Button>
            <Button href="/docs" variant="ghost">
              Docs / Help
            </Button>
          </div>

          <div className="mt-8 grid gap-3 sm:grid-cols-3">
            <div className="rounded-2xl border border-[#d7d3c8] bg-[#f7f5ef] px-4 py-3 text-xs text-[#4f6f6b]">
              Read-only viewer
            </div>
            <div className="rounded-2xl border border-[#d7d3c8] bg-[#f7f5ef] px-4 py-3 text-xs text-[#4f6f6b]">
              Server-side conversion
            </div>
            <div className="rounded-2xl border border-[#d7d3c8] bg-[#f7f5ef] px-4 py-3 text-xs text-[#4f6f6b]">
              Secure share links
            </div>
          </div>
        </div>

        <div className="relative">
          <div className="rounded-3xl border border-[#d7d3c8] bg-[#f7f5ef] p-5 shadow-sm">
            <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-[0.2em] text-[#4f6f6b]">
              <span>Viewer Preview</span>
              <span className="rounded-full border border-[#d7d3c8] bg-white px-2 py-1 text-[10px]">
                Read-only
              </span>
            </div>
            <div className="mt-4 overflow-hidden rounded-2xl border border-[#e3dfd3] bg-white">
              <Image
                src="/preview.svg"
                alt="Stellcodex viewer preview"
                width={900}
                height={560}
                className="h-auto w-full"
                priority
              />
            </div>
            <div className="mt-4 grid grid-cols-3 gap-2 text-xs text-[#4f6f6b]">
              <div className="rounded-xl border border-[#e3dfd3] bg-white px-3 py-2 text-center">
                Orbit
              </div>
              <div className="rounded-xl border border-[#e3dfd3] bg-white px-3 py-2 text-center">
                Measure
              </div>
              <div className="rounded-xl border border-[#e3dfd3] bg-white px-3 py-2 text-center">
                Share
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="mt-14 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="rounded-3xl border border-[#d7d3c8] bg-white/70 p-6 shadow-sm">
          <div className="text-sm font-semibold text-[#0c2a2a]">Tek bakista akış</div>
          <div className="mt-4 grid gap-3 text-sm text-[#2c4b49] sm:grid-cols-4">
            <div className="rounded-2xl border border-[#e3dfd3] bg-[#f7f5ef] px-3 py-3 text-center">
              Upload
            </div>
            <div className="rounded-2xl border border-[#e3dfd3] bg-[#f7f5ef] px-3 py-3 text-center">
              Convert
            </div>
            <div className="rounded-2xl border border-[#e3dfd3] bg-[#f7f5ef] px-3 py-3 text-center">
              View
            </div>
            <div className="rounded-2xl border border-[#e3dfd3] bg-[#f7f5ef] px-3 py-3 text-center">
              Share
            </div>
          </div>
        </div>

        <div className="rounded-3xl border border-[#d7d3c8] bg-[#0c3b3a] p-6 text-white shadow-sm">
          <div className="text-sm font-semibold">Dosya yuklemeden once</div>
          <p className="mt-2 text-sm text-white/80">
            STEP, IGES, STL, PDF, PNG, DXF ve daha fazlasi. Dosya yukleme ve
            goruntuleme akici, stabil ve guvenli.
          </p>
          <div className="mt-4">
            <Button href="/upload" variant="secondary">
              Yukleme ekranina git
            </Button>
          </div>
        </div>
      </section>

      <section className="mt-14">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.2em] text-[#4f6f6b]">
              Neden STELLCODEX
            </div>
            <h2 className="mt-3 text-2xl font-semibold text-[#0c2a2a] sm:text-3xl">
              CAD lisansi olmadan teknik kararlari hizlandir.
            </h2>
          </div>
          <Link className="text-sm font-semibold text-[#1d5a57] hover:text-[#0c2a2a]" href="/docs">
            Help center →
          </Link>
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-2">
          <div className="rounded-3xl border border-[#d7d3c8] bg-white/80 p-6 shadow-sm">
            <div className="text-sm font-semibold text-[#0c2a2a]">2D + 3D ayni yerde</div>
            <p className="mt-2 text-sm text-[#2c4b49]">
              Tek bir link ile teknik ekipten musteriye kadar herkes ayni modeli gorur.
            </p>
          </div>
          <div className="rounded-3xl border border-[#d7d3c8] bg-white/80 p-6 shadow-sm">
            <div className="text-sm font-semibold text-[#0c2a2a]">Guvenli paylasim</div>
            <p className="mt-2 text-sm text-[#2c4b49]">
              Read-only. Versiyon kontrolu ve paylasim limiti ile dosyalar kontrol altinda.
            </p>
          </div>
          <div className="rounded-3xl border border-[#d7d3c8] bg-white/80 p-6 shadow-sm">
            <div className="text-sm font-semibold text-[#0c2a2a]">Sunucu tarafi donusum</div>
            <p className="mt-2 text-sm text-[#2c4b49]">
              Kurulum yok. Donusum ve onizleme tek merkezden yapilir.
            </p>
          </div>
          <div className="rounded-3xl border border-[#d7d3c8] bg-white/80 p-6 shadow-sm">
            <div className="text-sm font-semibold text-[#0c2a2a]">Takim icin hazir</div>
            <p className="mt-2 text-sm text-[#2c4b49]">
              Dosya durumlari, goruntuleme baglantilari ve dashboard kontrol merkezi.
            </p>
          </div>
        </div>
      </section>

      <section className="mt-14 grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="rounded-3xl border border-[#d7d3c8] bg-[#f7f5ef] p-6 shadow-sm">
          <div className="text-sm font-semibold text-[#0c2a2a]">Kimler icin</div>
          <ul className="mt-3 grid gap-2 text-sm text-[#2c4b49]">
            <li>Endustriyel tasarim ve urun ekipleri</li>
            <li>Uretim ve teknik satin alma</li>
            <li>CAD lisansi olmayan yonetici ve tedarikciler</li>
            <li>Kalite ve teknik inceleme ekipleri</li>
          </ul>
        </div>

        <div className="rounded-3xl border border-[#d7d3c8] bg-white/80 p-6 shadow-sm">
          <div className="text-sm font-semibold text-[#0c2a2a]">Library / Community</div>
          <p className="mt-2 text-sm text-[#2c4b49]">
            Kurasyonlu model kitapligi, ornek dosyalar ve topluluk paylasimlari.
          </p>
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            {Array.from({ length: 3 }).map((_, idx) => (
              <div
                key={idx}
                className="rounded-2xl border border-dashed border-[#d7d3c8] bg-[#f7f5ef] px-3 py-6 text-center text-xs text-[#4f6f6b]"
              >
                Preview
              </div>
            ))}
          </div>
          <div className="mt-4">
            <Button href="/community" variant="secondary">
              Library sayfasina git
            </Button>
          </div>
        </div>
      </section>

      <section className="mt-14 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="rounded-3xl border border-[#d7d3c8] bg-white/80 p-6 shadow-sm">
          <div className="text-sm font-semibold text-[#0c2a2a]">Docs / Help</div>
          <p className="mt-2 text-sm text-[#2c4b49]">
            Kisa rehberler, format listeleri ve sorun giderme akislari tek yerde.
          </p>
          <div className="mt-4 flex flex-wrap gap-2 text-xs">
            <span className="rounded-full border border-[#d7d3c8] bg-[#f7f5ef] px-3 py-1">Getting started</span>
            <span className="rounded-full border border-[#d7d3c8] bg-[#f7f5ef] px-3 py-1">Formats</span>
            <span className="rounded-full border border-[#d7d3c8] bg-[#f7f5ef] px-3 py-1">Troubleshooting</span>
            <span className="rounded-full border border-[#d7d3c8] bg-[#f7f5ef] px-3 py-1">FAQ</span>
          </div>
        </div>

        <div className="rounded-3xl border border-[#d7d3c8] bg-[#0c3b3a] p-6 text-white shadow-sm">
          <div className="text-sm font-semibold">Guvenlik ve sinirlar</div>
          <ul className="mt-3 grid gap-2 text-sm text-white/80">
            <li>Read-only goruntuleme</li>
            <li>Paylasim linkleri kontrollu</li>
            <li>PII maskleme ve audit log</li>
            <li>KVKK / GDPR uyumlu altyapi</li>
          </ul>
        </div>
      </section>

      <section className="mt-14 rounded-3xl border border-[#d7d3c8] bg-[#f7f5ef] p-8 text-center shadow-sm">
        <h3 className="text-2xl font-semibold text-[#0c2a2a] sm:text-3xl">
          Dosyayi yukle, aninda goruntule.
        </h3>
        <p className="mt-2 text-sm text-[#2c4b49]">
          Stellcodex bir pazarlama sitesi degil, urunun kendisi.
        </p>
        <div className="mt-5 flex flex-wrap justify-center gap-3">
          <Button href="/upload">Simdi dosya yukle</Button>
          <Button href="/login" variant="secondary">
            Giris yap
          </Button>
        </div>
      </section>
    </main>
  );
}
