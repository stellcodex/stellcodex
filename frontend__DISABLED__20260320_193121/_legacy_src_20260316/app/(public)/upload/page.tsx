"use client";

import { UploadDrop } from "@/components/upload/UploadDrop";

export default function UploadPage() {
  return (
    <main className="mx-auto max-w-5xl px-6 py-8">
      <header className="max-w-xl">
        <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Upload</div>
        <h1 className="mt-4 text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">Drop one file. Keep moving.</h1>
      </header>

      <section className="mt-6">
        <UploadDrop />
      </section>
    </main>
  );
}
