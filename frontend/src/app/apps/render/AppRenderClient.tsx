"use client";

import { useState } from "react";
import { LayoutShell } from "@/components/layout/LayoutShell";
import { AppSwitcher } from "@/components/apps/AppSwitcher";
import { ScxContextHeader } from "@/components/apps/ScxContextHeader";
import { EmptyState } from "@/components/common/EmptyState";
import { useScxContext } from "@/components/common/useScxContext";
import { RENDER_PRESETS } from "@/data/render-presets.generated";
import { requestRenderPreset } from "@/services/api";

export default function AppRenderClient() {
  const context = useScxContext();
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!context.scx) {
    return (
      <LayoutShell>
        <EmptyState
          title="Dosya seçili değil"
          description="Render için bir dosya seçin."
          primaryCta={{ label: "Projeler", href: "/projects" }}
          secondaryCta={{ label: "Dosyalar", href: "/files" }}
        />
      </LayoutShell>
    );
  }

  return (
    <LayoutShell>
      <div className="flex flex-col gap-sectionGap">
        <AppSwitcher />
        <ScxContextHeader fileName={context.scx} format="GLB" status="Hazır" />
        <div className="flex flex-col gap-cardGap rounded-r2 border-soft bg-surface px-cardPad py-cardPad">
          <div className="text-fs1 font-medium">Önayar</div>
          <div className="flex flex-wrap gap-cardGap">
            {RENDER_PRESETS.map((preset) => (
              <button
                key={preset.name}
                className="h-btnH rounded-r1 border-soft bg-surface px-sp3 text-fs0"
                disabled={busy}
                onClick={async () => {
                  if (!context.scx) return;
                  setError(null);
                  setStatus("Render kuyruğa alındı...");
                  setBusy(true);
                  try {
                    await requestRenderPreset(context.scx, preset.name);
                    setStatus(`Önayar sıraya alındı: ${preset.label}`);
                  } catch (e: any) {
                    setError(e?.message || "Render isteği başarısız.");
                  } finally {
                    setBusy(false);
                  }
                }}
              >
                {preset.label}
              </button>
            ))}
          </div>
          <div className="rounded-r2 border-soft bg-surface2 px-cardPad py-cardPad text-fs1 text-muted">
            Render önizleme (yer tutucu)
          </div>
          {status ? <div className="text-xs text-muted">{status}</div> : null}
          {error ? <div className="text-xs text-red-600">{error}</div> : null}
        </div>
      </div>
    </LayoutShell>
  );
}
