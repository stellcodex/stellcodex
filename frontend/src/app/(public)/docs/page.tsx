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
    <main className="mx-auto max-w-6xl px-6 pb-16 pt-14">
      <header className="max-w-2xl">
        <div className="text-xs font-semibold uppercase tracking-[0.2em] text-[#4f6f6b]">
          Docs / Help
        </div>
        <h1 className="mt-4 text-3xl font-semibold tracking-tight text-[#0c2a2a] sm:text-4xl">
          Yardim ve dokumantasyon
        </h1>
        <p className="mt-3 text-sm text-[#2c4b49]">
          Getting started, format listeleri, sorun giderme ve SSS burada.
        </p>
      </header>

      <section className="mt-8 rounded-3xl border border-[#d7d3c8] bg-white/80 p-6 shadow-sm">
        <div className="text-sm font-semibold text-[#0c2a2a]">Getting Started</div>
        <p className="mt-2 text-sm text-[#2c4b49]">Upload → View → Share.</p>
      </section>

      <section className="mt-6 rounded-3xl border border-[#d7d3c8] bg-white/80 p-6 shadow-sm">
        <div className="text-sm font-semibold text-[#0c2a2a]">Supported Formats</div>
        <p className="mt-2 text-sm text-[#2c4b49]">
          Refer to <code className="rounded bg-[#f0eee7] px-2 py-1">docs/compatibility/formats-matrix.md</code>.
        </p>
      </section>

      <section className="mt-6 rounded-3xl border border-[#d7d3c8] bg-white/80 p-6 shadow-sm">
        <div className="text-sm font-semibold text-[#0c2a2a]">Troubleshooting</div>
        <p className="mt-2 text-sm text-[#2c4b49]">Content will be added as issues are documented.</p>
      </section>

      <section className="mt-6 rounded-3xl border border-[#d7d3c8] bg-white/80 p-6 shadow-sm">
        <div className="text-sm font-semibold text-[#0c2a2a]">FAQ</div>
        <p className="mt-2 text-sm text-[#2c4b49]">FAQ will appear after launch feedback.</p>
      </section>

      <section className="mt-8 rounded-3xl border border-[#d7d3c8] bg-white/80 p-6 shadow-sm">
        <div className="text-sm font-semibold text-[#0c2a2a]">Repo docs index</div>
        {docs.length === 0 ? (
          <p className="mt-3 text-sm text-[#2c4b49]">
            No docs detected. Ensure <code className="rounded bg-[#f0eee7] px-2 py-1">docs/</code> exists.
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
