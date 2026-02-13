import fs from "fs";
import path from "path";

function readMarkdown(filename: string) {
  try {
    const filePath = path.join(process.cwd(), "src", "content", filename);
    return fs.readFileSync(filePath, "utf-8");
  } catch {
    return "İçerik mevcut değil.";
  }
}

export default function PrivacyPage() {
  const tr = readMarkdown("privacy.tr.md");

  return (
    <main className="mx-auto max-w-6xl px-6 py-6 sm:py-8">
      <header className="max-w-2xl">
        <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
          Gizlilik
        </div>
        <h1 className="mt-4 text-xl font-semibold tracking-tight text-slate-900 sm:text-2xl">
          Gizlilik politikası
        </h1>
        <p className="mt-3 text-sm text-slate-600">
          Hukuki içerik markdown dosyalarından yüklenir.
        </p>
      </header>

      <section className="mt-8 grid gap-4">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="text-sm font-semibold text-slate-900">Türkçe</div>
          <pre className="mt-3 whitespace-pre-wrap text-sm text-slate-600">{tr}</pre>
        </div>
      </section>
    </main>
  );
}
