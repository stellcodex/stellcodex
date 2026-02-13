"use client";

import { LayoutShell } from "@/components/layout/LayoutShell";
import Link from "next/link";

export default function NewChatPage() {
  const newId = "new";
  return (
    <LayoutShell>
      <div className="flex flex-col gap-sectionGap">
        <div className="text-fs2 font-semibold">Yeni Sohbet</div>
        <div className="text-fs1 text-muted">Yeni bir konuşma başlat.</div>
        <Link href={`/chats/${newId}`} className="h-btnH rounded-r1 bg-accent px-sp3 text-fs1 font-medium text-bg">
          Konuşmayı aç
        </Link>
      </div>
    </LayoutShell>
  );
}
