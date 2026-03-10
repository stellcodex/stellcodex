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
          Docs
        </div>
        <h1 className="mt-4 text-xl font-semibold tracking-tight text-[#0c2a2a] sm:text-2xl">
          Help and documentation
        </h1>
        <p className="mt-3 text-sm text-[#2c4b49]">
          Getting started guides, format lists, troubleshooting notes, and FAQ live here.
        </p>
      </header>

      <section className="mt-8 rounded-3xl border border-[#d7d3c8] bg-white/80 p-5 shadow-sm">
        <div className="text-sm font-semibold text-[#0c2a2a]">Getting Started</div>
        <p className="mt-2 text-sm text-[#2c4b49]">Upload -> View -> Share.</p>
      </section>

      <section className="mt-6 rounded-3xl border border-[#d7d3c8] bg-white/80 p-5 shadow-sm">
        <div className="text-sm font-semibold text-[#0c2a2a]">Supported Formats</div>
        <p className="mt-2 text-sm text-[#2c4b49]">
          For details, review{" "}
          <code className="rounded bg-[#f0eee7] px-2 py-1">docs/compatibility/formats-matrix.md</code>{" "}
          in the repository.
        </p>
      </section>

      <section className="mt-6 rounded-3xl border border-[#d7d3c8] bg-white/80 p-5 shadow-sm">
        <div className="text-sm font-semibold text-[#0c2a2a]">Troubleshooting</div>
        <p className="mt-2 text-sm text-[#2c4b49]">
          Additional guides will be added as known issues are documented.
        </p>
      </section>

      <section className="mt-6 rounded-3xl border border-[#d7d3c8] bg-white/80 p-5 shadow-sm">
        <div className="text-sm font-semibold text-[#0c2a2a]">FAQ</div>
        <p className="mt-2 text-sm text-[#2c4b49]">
          FAQ entries will grow from real usage feedback after release.
        </p>
      </section>

      <section className="mt-8 rounded-3xl border border-[#d7d3c8] bg-white/80 p-5 shadow-sm">
        <div className="text-sm font-semibold text-[#0c2a2a]">Repository document index</div>
        {docs.length === 0 ? (
          <p className="mt-3 text-sm text-[#2c4b49]">
            No documents were found. Check the{" "}
            <code className="rounded bg-[#f0eee7] px-2 py-1">docs/</code> directory.
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
