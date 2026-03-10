"use client";

import { UploadDrop } from "@/components/upload/UploadDrop";

export default function UploadPage() {
  return (
    <main className="mx-auto max-w-6xl px-6 py-6 sm:py-8">
      <header className="max-w-2xl">
        <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
          Upload
        </div>
        <h1 className="mt-4 text-xl font-semibold tracking-tight text-slate-900 sm:text-2xl">
          Upload a file and open the right application immediately.
        </h1>
        <p className="mt-3 text-sm text-slate-600">
          STELLCODEX routes 3D, 2D, and document files into the responsible workspace automatically.
        </p>
      </header>

      <section className="mt-8">
        <UploadDrop />
      </section>
    </main>
  );
}
