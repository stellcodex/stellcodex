import fs from "fs";
import path from "path";

function readMarkdown(filename: string) {
  try {
    const filePath = path.join(process.cwd(), "src", "content", filename);
    return fs.readFileSync(filePath, "utf-8");
  } catch {
    return "Content not available.";
  }
}

export default function TermsPage() {
  const tr = readMarkdown("terms.tr.md");
  const en = readMarkdown("terms.en.md");

  return (
    <main className="mx-auto max-w-6xl px-6 py-12">
      <header className="max-w-2xl">
        <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
          Terms
        </div>
        <h1 className="mt-4 text-3xl font-semibold tracking-tight text-slate-900 sm:text-4xl">
          Terms of service
        </h1>
        <p className="mt-3 text-sm text-slate-600">
          Legal content is loaded from markdown files for bilingual updates.
        </p>
      </header>

      <section className="mt-8 grid gap-6">
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="text-sm font-semibold text-slate-900">Türkçe</div>
          <pre className="mt-3 whitespace-pre-wrap text-sm text-slate-600">{tr}</pre>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="text-sm font-semibold text-slate-900">English</div>
          <pre className="mt-3 whitespace-pre-wrap text-sm text-slate-600">{en}</pre>
        </div>
      </section>
    </main>
  );
}
