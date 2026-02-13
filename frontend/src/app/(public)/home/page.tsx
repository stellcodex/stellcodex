import Image from "next/image";
import Link from "next/link";
import { Button } from "@/components/ui/Button";

export default function HomePage() {
  return (
    <main className="mx-auto max-w-6xl px-6 py-6 sm:py-8">
      <section className="grid gap-4 lg:grid-cols-[1.15fr_0.85fr]">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full border border-[#d7d3c8] bg-[#f7f5ef] px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-[#4f6f6b]">
            STELLCODEX MÜHENDİSLİK GÖRÜNTÜLEYİCİ
          </div>
          <h1 className="mt-4 text-xl font-semibold tracking-tight text-[#0c2a2a] sm:text-2xl">
            Görüntüle. İncele. Paylaş. CAD&apos;siz mühendislik verisi.
          </h1>
          <p className="mt-4 max-w-xl text-sm text-[#2c4b49]">
            Endüstriyel tasarımcılar, imalat ekipleri ve CAD lisansı olmayan karar
            vericiler için. Dosyayı yükle, 2D/3D görüntüle, link ile paylaş.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Button href="/upload">Dosya Yükle</Button>
            <Button href="/community" variant="secondary">
              Topluluk
            </Button>
            <Button href="/docs" variant="ghost">
              Dokümanlar
            </Button>
          </div>

          <div className="mt-8 grid gap-3 sm:grid-cols-3">
            <div className="rounded-2xl border border-[#d7d3c8] bg-[#f7f5ef] px-4 py-3 text-xs text-[#4f6f6b]">
              Salt görüntüleme
            </div>
            <div className="rounded-2xl border border-[#d7d3c8] bg-[#f7f5ef] px-4 py-3 text-xs text-[#4f6f6b]">
              Sunucu tarafı dönüşüm
            </div>
            <div className="rounded-2xl border border-[#d7d3c8] bg-[#f7f5ef] px-4 py-3 text-xs text-[#4f6f6b]">
              Güvenli paylaşım linkleri
            </div>
          </div>
        </div>

        <div className="relative">
          <div className="rounded-3xl border border-[#d7d3c8] bg-[#f7f5ef] p-5 shadow-sm">
            <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-[0.2em] text-[#4f6f6b]">
              <span>Görüntüleyici Önizleme</span>
              <span className="rounded-full border border-[#d7d3c8] bg-white px-2 py-1 text-[10px]">
                Salt görüntüleme
              </span>
            </div>
            <div className="mt-4 overflow-hidden rounded-2xl border border-[#e3dfd3] bg-white">
              <Image
                src="/preview.svg"
                alt="Stellcodex görüntüleyici önizleme"
                width={900}
                height={560}
                className="h-auto w-full"
                priority
              />
            </div>
            <div className="mt-4 grid grid-cols-3 gap-2 text-xs text-[#4f6f6b]">
              <div className="rounded-xl border border-[#e3dfd3] bg-white px-3 py-2 text-center">
                Yörünge
              </div>
              <div className="rounded-xl border border-[#e3dfd3] bg-white px-3 py-2 text-center">
                Ölçüm
              </div>
              <div className="rounded-xl border border-[#e3dfd3] bg-white px-3 py-2 text-center">
                Paylaş
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="mt-10 grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="rounded-3xl border border-[#d7d3c8] bg-white/70 p-5 shadow-sm">
          <div className="text-sm font-semibold text-[#0c2a2a]">Tek bakışta akış</div>
          <div className="mt-4 grid gap-3 text-sm text-[#2c4b49] sm:grid-cols-4">
            <div className="rounded-2xl border border-[#e3dfd3] bg-[#f7f5ef] px-3 py-3 text-center">
              Yükle
            </div>
            <div className="rounded-2xl border border-[#e3dfd3] bg-[#f7f5ef] px-3 py-3 text-center">
              Dönüştür
            </div>
            <div className="rounded-2xl border border-[#e3dfd3] bg-[#f7f5ef] px-3 py-3 text-center">
              Görüntüle
            </div>
            <div className="rounded-2xl border border-[#e3dfd3] bg-[#f7f5ef] px-3 py-3 text-center">
              Paylaş
            </div>
          </div>
        </div>

        <div className="rounded-3xl border border-[#d7d3c8] bg-[#0c3b3a] p-5 text-white shadow-sm">
          <div className="text-sm font-semibold">Dosya yüklemeden önce</div>
          <p className="mt-2 text-sm text-white/80">
            STEP, IGES, STL, PDF, PNG, DXF ve daha fazlası. Dosya yükleme ve
            görüntüleme akıcı, stabil ve güvenli.
          </p>
          <div className="mt-4">
            <Button href="/upload" variant="secondary">
              Yükleme ekranına git
            </Button>
          </div>
        </div>
      </section>

      <section className="mt-10">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.2em] text-[#4f6f6b]">
              Neden STELLCODEX
            </div>
            <h2 className="mt-3 text-xl font-semibold text-[#0c2a2a] sm:text-2xl">
              CAD lisansı olmadan teknik kararları hızlandır.
            </h2>
          </div>
          <Link className="text-sm font-semibold text-[#1d5a57] hover:text-[#0c2a2a]" href="/docs">
            Yardım merkezi →
          </Link>
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-2">
          <div className="rounded-3xl border border-[#d7d3c8] bg-white/80 p-5 shadow-sm">
            <div className="text-sm font-semibold text-[#0c2a2a]">2D + 3D aynı yerde</div>
            <p className="mt-2 text-sm text-[#2c4b49]">
              Tek bir link ile teknik ekipten müşteriye kadar herkes aynı modeli görür.
            </p>
          </div>
          <div className="rounded-3xl border border-[#d7d3c8] bg-white/80 p-5 shadow-sm">
            <div className="text-sm font-semibold text-[#0c2a2a]">Güvenli paylaşım</div>
            <p className="mt-2 text-sm text-[#2c4b49]">
              Salt görüntüleme. Versiyon kontrolü ve paylaşım limiti ile dosyalar kontrol altında.
            </p>
          </div>
          <div className="rounded-3xl border border-[#d7d3c8] bg-white/80 p-5 shadow-sm">
            <div className="text-sm font-semibold text-[#0c2a2a]">Sunucu tarafı dönüşüm</div>
            <p className="mt-2 text-sm text-[#2c4b49]">
              Kurulum yok. Dönüşüm ve önizleme tek merkezden yapılır.
            </p>
          </div>
          <div className="rounded-3xl border border-[#d7d3c8] bg-white/80 p-5 shadow-sm">
            <div className="text-sm font-semibold text-[#0c2a2a]">Takım için hazır</div>
            <p className="mt-2 text-sm text-[#2c4b49]">
              Dosya durumları, görüntüleme bağlantıları ve kontrol merkezi.
            </p>
          </div>
        </div>
      </section>

      <section className="mt-10 grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="rounded-3xl border border-[#d7d3c8] bg-[#f7f5ef] p-5 shadow-sm">
          <div className="text-sm font-semibold text-[#0c2a2a]">Kimler için</div>
          <ul className="mt-3 grid gap-2 text-sm text-[#2c4b49]">
            <li>Endüstriyel tasarım ve ürün ekipleri</li>
            <li>Üretim ve teknik satın alma</li>
            <li>CAD lisansı olmayan yönetici ve tedarikçiler</li>
            <li>Kalite ve teknik inceleme ekipleri</li>
          </ul>
        </div>

        <div className="rounded-3xl border border-[#d7d3c8] bg-white/80 p-5 shadow-sm">
          <div className="text-sm font-semibold text-[#0c2a2a]">Topluluk</div>
          <p className="mt-2 text-sm text-[#2c4b49]">
            Kurasyonlu model kitaplığı, örnek dosyalar ve topluluk paylaşımları.
          </p>
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            {Array.from({ length: 3 }).map((_, idx) => (
              <div
                key={idx}
                className="rounded-2xl border border-dashed border-[#d7d3c8] bg-[#f7f5ef] px-3 py-6 text-center text-xs text-[#4f6f6b]"
              >
                Önizleme
              </div>
            ))}
          </div>
          <div className="mt-4">
            <Button href="/community" variant="secondary">
              Topluluk sayfasına git
            </Button>
          </div>
        </div>
      </section>

      <section className="mt-10 grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="rounded-3xl border border-[#d7d3c8] bg-white/80 p-5 shadow-sm">
          <div className="text-sm font-semibold text-[#0c2a2a]">Dokümanlar</div>
          <p className="mt-2 text-sm text-[#2c4b49]">
            Kısa rehberler, format listeleri ve sorun giderme akışları tek yerde.
          </p>
          <div className="mt-4 flex flex-wrap gap-2 text-xs">
            <span className="rounded-full border border-[#d7d3c8] bg-[#f7f5ef] px-3 py-1">Başlangıç</span>
            <span className="rounded-full border border-[#d7d3c8] bg-[#f7f5ef] px-3 py-1">Formatlar</span>
            <span className="rounded-full border border-[#d7d3c8] bg-[#f7f5ef] px-3 py-1">Sorun giderme</span>
            <span className="rounded-full border border-[#d7d3c8] bg-[#f7f5ef] px-3 py-1">SSS</span>
          </div>
        </div>

        <div className="rounded-3xl border border-[#d7d3c8] bg-[#0c3b3a] p-5 text-white shadow-sm">
          <div className="text-sm font-semibold">Güvenlik ve sınırlar</div>
          <ul className="mt-3 grid gap-2 text-sm text-white/80">
            <li>Salt görüntüleme</li>
            <li>Paylaşım linkleri kontrollü</li>
            <li>PII maskeleme ve denetim kaydı</li>
            <li>KVKK / GDPR uyumlu altyapı</li>
          </ul>
        </div>
      </section>

      <section className="mt-10 rounded-3xl border border-[#d7d3c8] bg-[#f7f5ef] p-5 text-center shadow-sm">
        <h3 className="text-xl font-semibold text-[#0c2a2a] sm:text-2xl">
          Dosyayı yükle, anında görüntüle.
        </h3>
        <p className="mt-2 text-sm text-[#2c4b49]">
          Stellcodex bir pazarlama sitesi değil, ürünün kendisi.
        </p>
        <div className="mt-5 flex flex-wrap justify-center gap-3">
          <Button href="/upload">Şimdi dosya yükle</Button>
          <Button href="/login" variant="secondary">
            Giriş yap
          </Button>
        </div>
      </section>
    </main>
  );
}
