"use client";

import { useMemo, useState } from "react";
import { Button } from "@/components/common/Button";

function dataDownload(name: string, content: string) {
  return `data:text/plain;charset=utf-8,${encodeURIComponent(`# ${name}\n${content}\n`)}`;
}

export function MoldWorkspace() {
  const [material, setMaterial] = useState("P20");
  const [cavityCount, setCavityCount] = useState("1");
  const [parting, setParting] = useState("Tek Yüzey");
  const [runner, setRunner] = useState("Soğuk Yolluk");

  const summary = useMemo(
    () => ({ material, cavityCount, parting, runner }),
    [material, cavityCount, parting, runner]
  );

  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,420px)_minmax(0,1fr)]">
      <div className="rounded-2xl border border-slate-200 bg-white p-4">
        <h1 className="text-lg font-semibold text-slate-900">MoldCodes</h1>
        <p className="mt-1 text-sm text-slate-600">Toolbox / parametric configuration (V1)</p>
        <div className="mt-4 grid gap-3">
          <label className="grid gap-1 text-sm">
            <span className="text-slate-600">Kalıp çeliği</span>
            <select
              value={material}
              onChange={(e) => setMaterial(e.target.value)}
              className="h-10 rounded-xl border border-slate-200 px-3"
            >
              <option>P20</option>
              <option>H13</option>
              <option>1.2311</option>
              <option>1.2344</option>
            </select>
          </label>
          <label className="grid gap-1 text-sm">
            <span className="text-slate-600">Göz sayısı</span>
            <select
              value={cavityCount}
              onChange={(e) => setCavityCount(e.target.value)}
              className="h-10 rounded-xl border border-slate-200 px-3"
            >
              <option>1</option>
              <option>2</option>
              <option>4</option>
              <option>8</option>
            </select>
          </label>
          <label className="grid gap-1 text-sm">
            <span className="text-slate-600">Ayrım tipi</span>
            <select
              value={parting}
              onChange={(e) => setParting(e.target.value)}
              className="h-10 rounded-xl border border-slate-200 px-3"
            >
              <option>Tek Yüzey</option>
              <option>Çoklu Ayrım</option>
            </select>
          </label>
          <label className="grid gap-1 text-sm">
            <span className="text-slate-600">Yolluk tipi</span>
            <select
              value={runner}
              onChange={(e) => setRunner(e.target.value)}
              className="h-10 rounded-xl border border-slate-200 px-3"
            >
              <option>Soğuk Yolluk</option>
              <option>Sıcak Yolluk</option>
            </select>
          </label>
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          <Button
            href={dataDownload("mold-output.step", JSON.stringify(summary, null, 2))}
            variant="primary"
            download="mold-output.step"
          >
            STEP indir
          </Button>
          <Button
            href={dataDownload("mold-output.scx", JSON.stringify(summary, null, 2))}
            download="mold-output.scx"
          >
            SCX indir
          </Button>
        </div>

        <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-3">
          <div className="text-sm font-medium text-slate-800">Otomatik kalıplama (V2)</div>
          <p className="mt-1 text-sm text-slate-500">Coming soon / disabled placeholder</p>
          <button disabled className="mt-3 h-10 rounded-xl border border-slate-200 px-4 text-sm text-slate-400">
            V2 Yakında
          </button>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-4">
        <div className="mb-3 text-sm font-medium text-slate-700">Embedded 3D Preview</div>
        <div className="grid min-h-[520px] place-items-center rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
          <div>
            <div className="text-sm font-semibold text-slate-900">Mold Preview Placeholder</div>
            <div className="mt-2 text-sm text-slate-600">
              {summary.cavityCount} göz · {summary.material} · {summary.runner}
            </div>
            <div className="mt-4 grid gap-1 text-xs text-slate-500">
              <div>Ayrım: {summary.parting}</div>
              <div>V1 toolbox preview (placeholder viewer)</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

