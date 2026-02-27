"use client";

import { useRouter } from "next/navigation";
import { UploadDrop } from "@/components/upload/UploadDrop";

export default function UploadPage() {
  const router = useRouter();

  return (
    <main className="mx-auto max-w-6xl px-6 py-6 sm:py-8">
      <header className="max-w-2xl">
        <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
          Yükleme
        </div>
        <h1 className="mt-4 text-xl font-semibold tracking-tight text-slate-900 sm:text-2xl">
          Dosya yükle ve hemen görüntüle.
        </h1>
        <p className="mt-3 text-sm text-slate-600">
          Yükleme başlar başlamaz işleme alınır ve otomatik görüntüleme açılır.
        </p>
      </header>

      <section className="mt-8">
        <UploadDrop
          onUploaded={(fileId) => {
            router.push(`/view/${fileId}`);
          }}
        />
      </section>
    </main>
  );
}
