"use client";

import { useRouter } from "next/navigation";
import { UploadDrop } from "@/components/upload/UploadDrop";

export default function UploadPage() {
  const router = useRouter();

  return (
    <main className="mx-auto max-w-3xl px-6 pb-16 pt-14">
      <header className="max-w-xl">
        <div className="text-xs font-semibold uppercase tracking-[0.2em] text-[#4f6f6b]">Upload</div>
        <h1 className="mt-3 text-3xl font-semibold text-[#0c2a2a] sm:text-4xl">
          Dosyayi yukle
        </h1>
        <p className="mt-2 text-sm text-[#2c4b49]">
          Yukleme baslar baslamaz isleme alinir ve otomatik goruntuleme acilir.
        </p>
      </header>

      <section className="mt-8">
        <UploadDrop onUploaded={(fileId) => router.push(`/view/${fileId}`)} />
      </section>
    </main>
  );
}
