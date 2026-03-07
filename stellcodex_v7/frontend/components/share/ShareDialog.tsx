"use client";

import { useMemo, useState } from "react";
import { Button } from "@/components/common/Button";
import { Modal } from "@/components/common/Modal";
import { createShare } from "@/lib/api";

export function ShareDialog({
  open,
  fileId,
  onClose,
}: {
  open: boolean;
  fileId: string;
  onClose: () => void;
}) {
  const [canView, setCanView] = useState(true);
  const [canDownload, setCanDownload] = useState(false);
  const [password, setPassword] = useState("");
  const [expiryHours, setExpiryHours] = useState<string>("");
  const [shareUrl, setShareUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const expiresAt = useMemo(() => {
    const hours = Number(expiryHours);
    if (!hours || Number.isNaN(hours) || hours <= 0) return undefined;
    return new Date(Date.now() + hours * 60 * 60 * 1000).toISOString();
  }, [expiryHours]);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    try {
      const result = await createShare(fileId, {
        canView,
        canDownload,
        password: password || undefined,
        expiresAt,
      });
      const absolute = typeof window !== "undefined" ? new URL(result.shareUrl, window.location.origin).toString() : result.shareUrl;
      setShareUrl(absolute);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Paylaşım linki üretilemedi.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal open={open} title="Paylaşım Oluştur" onClose={onClose}>
      <div className="grid gap-4">
        <label className="flex items-center gap-2 text-sm text-slate-700">
          <input type="checkbox" checked={canView} onChange={(e) => setCanView(e.target.checked)} />
          Görüntüleme izni
        </label>
        <label className="flex items-center gap-2 text-sm text-slate-700">
          <input
            type="checkbox"
            checked={canDownload}
            onChange={(e) => setCanDownload(e.target.checked)}
          />
          İndirme izni
        </label>
        <label className="grid gap-1 text-sm">
          <span className="text-slate-600">Şifre (opsiyonel)</span>
          <input
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="h-10 rounded-xl border border-slate-200 px-3"
            placeholder="İsteğe bağlı"
          />
        </label>
        <label className="grid gap-1 text-sm">
          <span className="text-slate-600">Süre / saat (opsiyonel)</span>
          <input
            value={expiryHours}
            onChange={(e) => setExpiryHours(e.target.value)}
            className="h-10 rounded-xl border border-slate-200 px-3"
            inputMode="numeric"
            placeholder="24"
          />
        </label>

        <div className="flex gap-2">
          <Button variant="primary" onClick={handleGenerate} disabled={loading}>
            {loading ? "Üretiliyor..." : "Link Üret"}
          </Button>
          {shareUrl ? (
            <Button
              onClick={async () => {
                await navigator.clipboard.writeText(shareUrl);
              }}
            >
              Linki Kopyala
            </Button>
          ) : null}
        </div>

        {shareUrl ? (
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm break-all">{shareUrl}</div>
        ) : null}
        {error ? <p className="text-sm text-red-600">{error}</p> : null}
      </div>
    </Modal>
  );
}

