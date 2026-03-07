"use client";

import { useEffect } from "react";
import { ErrorState } from "@/components/ui/StateBlocks";
import { Button } from "@/components/ui/Button";

const CHUNK_RELOAD_KEY = "scx_chunk_reload_once";

function isChunkLoadError(error: Error | null | undefined): boolean {
  const text = String(error?.message || "").toLowerCase();
  return (
    text.includes("failed to load chunk") ||
    text.includes("loading chunk") ||
    text.includes("/_next/static/chunks/")
  );
}

export default function GlobalError({ error, reset }: { error: Error; reset: () => void }) {
  const chunkError = isChunkLoadError(error);

  useEffect(() => {
    if (!chunkError) return;
    if (typeof window === "undefined") return;
    const attempted = window.sessionStorage.getItem(CHUNK_RELOAD_KEY) === "1";
    if (attempted) return;
    window.sessionStorage.setItem(CHUNK_RELOAD_KEY, "1");
    window.location.reload();
  }, [chunkError]);

  const message = chunkError
    ? "Yeni sürüm yayına alınmış olabilir. Sayfa yenileniyor; düzelmezse tarayıcı önbelleğini temizleyip tekrar deneyin."
    : error?.message || "Beklenmeyen hata.";

  return (
    <div className="mx-auto max-w-3xl px-6 py-8">
      <ErrorState
        title="Bir şeyler ters gitti"
        description={message}
        action={
          <Button
            variant="secondary"
            onClick={() => {
              if (typeof window !== "undefined") {
                window.sessionStorage.removeItem(CHUNK_RELOAD_KEY);
              }
              if (chunkError && typeof window !== "undefined") {
                window.location.reload();
                return;
              }
              reset();
            }}
          >
            {chunkError ? "Sayfayı yenile" : "Yeniden dene"}
          </Button>
        }
      />
    </div>
  );
}
