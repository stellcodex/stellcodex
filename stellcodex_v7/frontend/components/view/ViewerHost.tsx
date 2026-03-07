"use client";

import { useMemo, useState } from "react";
import type { ViewerEngine } from "@/lib/stellcodex/types";
import { Toolbar2D } from "@/components/view/Toolbars/Toolbar2D";
import { Toolbar3D } from "@/components/view/Toolbars/Toolbar3D";
import { ToolbarPDF } from "@/components/view/Toolbars/ToolbarPDF";
import { ToolbarImage } from "@/components/view/Toolbars/ToolbarImage";
import { ToolbarOffice } from "@/components/view/Toolbars/ToolbarOffice";

function EngineToolbar({ engine }: { engine: ViewerEngine }) {
  if (engine === "viewer3d") return <Toolbar3D />;
  if (engine === "viewer2d") return <Toolbar2D />;
  if (engine === "pdf") return <ToolbarPDF />;
  if (engine === "image") return <ToolbarImage />;
  if (engine === "office") return <ToolbarOffice />;
  return null;
}

export function ViewerHost({
  file,
  engine,
}: {
  file: { id: string; name: string; kind: string };
  engine: ViewerEngine;
}) {
  const [showMiniToolbar, setShowMiniToolbar] = useState(false);
  const placeholder = useMemo(() => {
    if (engine === "archive") return "Arşiv dosyaları StellShare içinde yönetilir.";
    if (engine === "unsupported") return "Bu format için görüntüleyici mevcut değil.";
    return "Preview not available (placeholder viewer)";
  }, [engine]);

  return (
    <div className="grid gap-3">
      <div className="rounded-2xl border border-slate-200 bg-white p-3">
        <EngineToolbar engine={engine} />
      </div>
      <div className="relative rounded-2xl border border-slate-200 bg-white p-4">
        <button
          className="grid min-h-[480px] w-full place-items-center rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center"
          onClick={() => setShowMiniToolbar((v) => !v)}
        >
          <div>
            <div className="text-sm font-semibold text-slate-900">{file.name}</div>
            <div className="mt-1 text-sm text-slate-500">
              {engine} · {file.kind}
            </div>
            <div className="mt-3 text-sm text-slate-600">{placeholder}</div>
            <div className="mt-3 text-xs text-slate-400">
              Model üstüne tıklama mini toolbar simülasyonu için alan.
            </div>
          </div>
        </button>
        {showMiniToolbar && (engine === "viewer3d" || engine === "viewer2d") ? (
          <div className="absolute right-6 top-6 flex gap-2 rounded-xl border border-slate-200 bg-white p-2 shadow-sm">
            <button className="rounded-lg border border-slate-200 px-2 py-1 text-xs">Ölçüm</button>
            <button className="rounded-lg border border-slate-200 px-2 py-1 text-xs">Kesit</button>
            <button className="rounded-lg border border-slate-200 px-2 py-1 text-xs">Explode</button>
          </div>
        ) : null}
      </div>
    </div>
  );
}

