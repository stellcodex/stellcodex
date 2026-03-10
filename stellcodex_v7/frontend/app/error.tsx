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
    ? "A newer release may have been deployed. The page is reloading; if the issue persists, clear the browser cache and try again."
    : error?.message || "Unexpected error.";

  return (
    <div className="mx-auto max-w-3xl px-6 py-8">
      <ErrorState
        title="Something went wrong"
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
            {chunkError ? "Reload page" : "Try again"}
          </Button>
        }
      />
    </div>
  );
}
