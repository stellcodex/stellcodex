import fs from "fs";
import path from "path";

function collectDocs(root: string, base: string, out: string[]) {
  const entries = fs.readdirSync(root, { withFileTypes: true });
  for (const entry of entries) {
    const full = path.join(root, entry.name);
    if (entry.isDirectory()) {
      collectDocs(full, base, out);
    } else if (entry.isFile() && entry.name.endsWith(".md")) {
      out.push(path.relative(base, full));
    }
  }
}

export default function DocsPage() {
  let docs: string[] = [];
  try {
    const docsRoot = path.join(process.cwd(), "..", "docs");
    collectDocs(docsRoot, docsRoot, docs);
    docs.sort();
  } catch {
    docs = [];
  }

  return (
    <main className="mx-auto max-w-6xl px-6 py-6 sm:py-8">
      <header className="max-w-2xl">
        <div className="text-xs font-semibold uppercase tracking-[0.2em] text-[#4f6f6b]">
          Dokümanlar
        </div>
        <h1 className="mt-4 text-xl font-semibold tracking-tight text-[#0c2a2a] sm:text-2xl">
          Yardım ve dokümantasyon
        </h1>
        <p className="mt-3 text-sm text-[#2c4b49]">
          Başlangıç, format listeleri, sorun giderme ve SSS burada.
        </p>
      </header>

      <section className="mt-8 rounded-3xl border border-[#d7d3c8] bg-white/80 p-5 shadow-sm">
        <div className="text-sm font-semibold text-[#0c2a2a]">Başlangıç</div>
        <p className="mt-2 text-sm text-[#2c4b49]">Yükle → Görüntüle → Paylaş.</p>
      </section>

      <section className="mt-6 rounded-3xl border border-[#d7d3c8] bg-white/80 p-5 shadow-sm">
        <div className="text-sm font-semibold text-[#0c2a2a]">Desteklenen Formatlar</div>
        <p className="mt-2 text-sm text-[#2c4b49]">
          Ayrıntı için{" "}
          <code className="rounded bg-[#f0eee7] px-2 py-1">docs/compatibility/formats-matrix.md</code>{" "}
          dosyasına bakın.
        </p>
      </section>

      <section className="mt-6 rounded-3xl border border-[#d7d3c8] bg-white/80 p-5 shadow-sm">
        <div className="text-sm font-semibold text-[#0c2a2a]">Sorun Giderme</div>
        <p className="mt-2 text-sm text-[#2c4b49]">
          Sorunlar belgelendikçe içerik eklenecektir.
        </p>
      </section>

      <section className="mt-6 rounded-3xl border border-[#d7d3c8] bg-white/80 p-5 shadow-sm">
        <div className="text-sm font-semibold text-[#0c2a2a]">SSS</div>
        <p className="mt-2 text-sm text-[#2c4b49]">
          SSS, yayından sonraki geri bildirimlerle oluşacaktır.
        </p>
      </section>

      <section className="mt-8 rounded-3xl border border-[#d7d3c8] bg-white/80 p-5 shadow-sm">
        <div className="text-sm font-semibold text-[#0c2a2a]">Repo doküman listesi</div>
        {docs.length === 0 ? (
          <p className="mt-3 text-sm text-[#2c4b49]">
            Doküman bulunamadı.{" "}
            <code className="rounded bg-[#f0eee7] px-2 py-1">docs/</code> klasörünü kontrol edin.
          </p>
        ) : (
          <ul className="mt-4 grid gap-2 text-sm text-[#2c4b49]">
            {docs.map((doc) => (
              <li key={doc} className="rounded-lg border border-[#e3dfd3] bg-[#f7f5ef] px-3 py-2">
                {doc}
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
