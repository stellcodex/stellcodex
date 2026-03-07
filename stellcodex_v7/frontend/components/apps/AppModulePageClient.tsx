"use client";

import { useEffect, useMemo, useState } from "react";

import { AppShell } from "@/components/shell/AppShell";
import {
  getAppManifest,
  getFileDecisionJson,
  listAppsCatalog,
  listFiles,
  type AppManifestResponse,
  type AppsCatalogItem,
  type DecisionJsonResponse,
  type FileItem,
} from "@/services/api";

type Props = {
  slug: string;
};

function pretty(value: unknown) {
  return JSON.stringify(value, null, 2);
}

export function AppModulePageClient({ slug }: Props) {
  const [catalogItem, setCatalogItem] = useState<AppsCatalogItem | null>(null);
  const [manifest, setManifest] = useState<AppManifestResponse | null>(null);
  const [files, setFiles] = useState<FileItem[]>([]);
  const [projectId, setProjectId] = useState("default");
  const [fileId, setFileId] = useState("");
  const [decision, setDecision] = useState<DecisionJsonResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const [catalog, manifestResp, fileRows] = await Promise.all([
          listAppsCatalog(false),
          getAppManifest(slug),
          listFiles(),
        ]);
        if (!active) return;
        const item = catalog.find((row) => row.slug === slug) || null;
        setCatalogItem(item);
        setManifest(manifestResp);
        setFiles(fileRows);
        setFileId(fileRows[0]?.file_id || "");
        setError(null);
      } catch (err) {
        if (!active) return;
        setError(err instanceof Error ? err.message : "App modülü yüklenemedi.");
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [slug]);

  useEffect(() => {
    let active = true;
    if (!fileId) {
      setDecision(null);
      return;
    }
    (async () => {
      try {
        const payload = await getFileDecisionJson(fileId);
        if (!active) return;
        setDecision(payload);
      } catch {
        if (!active) return;
        setDecision(null);
      }
    })();
    return () => {
      active = false;
    };
  }, [fileId]);

  const fileOptions = useMemo(() => files.slice(0, 100), [files]);

  return (
    <AppShell section="apps">
      <div className="space-y-4">
        <div className="rounded-2xl border border-[#dbe3ec] bg-white p-4">
          <div className="flex flex-wrap items-center gap-3">
            <div className="min-w-[220px] flex-1">
              <div className="text-xs uppercase tracking-[0.11em] text-[#5a738b]">project_id</div>
              <input
                value={projectId}
                onChange={(event) => setProjectId(event.target.value)}
                className="mt-1 w-full rounded-lg border border-[#ced9e6] px-3 py-2 text-sm"
                placeholder="default"
              />
            </div>
            <div className="min-w-[280px] flex-[2]">
              <div className="text-xs uppercase tracking-[0.11em] text-[#5a738b]">file_id</div>
              <select
                value={fileId}
                onChange={(event) => setFileId(event.target.value)}
                className="mt-1 w-full rounded-lg border border-[#ced9e6] px-3 py-2 text-sm"
              >
                <option value="">Dosya seçin</option>
                {fileOptions.map((file) => (
                  <option key={file.file_id} value={file.file_id}>
                    {file.file_id} • {file.original_name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {loading ? <div className="rounded-2xl border border-[#dbe3ec] bg-white p-4 text-sm">Yükleniyor...</div> : null}
        {error ? <div className="rounded-2xl border border-[#ef9a9a] bg-[#fff4f4] p-4 text-sm text-[#8a1f1f]">{error}</div> : null}

        <div className="grid gap-4 xl:grid-cols-[minmax(0,2fr)_minmax(320px,1fr)]">
          <section className="rounded-2xl border border-[#dbe3ec] bg-white p-4">
            <h1 className="text-xl font-semibold text-[#10243e]">{catalogItem?.name || slug}</h1>
            <p className="mt-2 text-sm text-[#4b657c]">
              Kategori: <strong>{catalogItem?.category || "unknown"}</strong> | Plan: <strong>{catalogItem?.tier || "n/a"}</strong>
            </p>
            <div className="mt-3 grid gap-3 md:grid-cols-2">
              <div className="rounded-lg border border-[#dbe3ec] bg-[#f7fbff] p-3">
                <div className="text-xs uppercase tracking-[0.1em] text-[#5f7690]">Required Capabilities</div>
                <ul className="mt-2 space-y-1 text-sm text-[#1d334b]">
                  {(catalogItem?.required_capabilities || []).map((cap) => (
                    <li key={cap}>{cap}</li>
                  ))}
                </ul>
              </div>
              <div className="rounded-lg border border-[#dbe3ec] bg-[#f7fbff] p-3">
                <div className="text-xs uppercase tracking-[0.1em] text-[#5f7690]">Supported Formats</div>
                <p className="mt-2 text-sm text-[#1d334b]">{(catalogItem?.supported_formats || []).join(", ")}</p>
              </div>
            </div>

            <div className="mt-3 rounded-lg border border-[#dbe3ec] bg-[#fbfdff] p-3">
              <div className="text-xs uppercase tracking-[0.1em] text-[#5f7690]">Manifest</div>
              <pre className="mt-2 max-h-[420px] overflow-auto text-xs text-[#18314b]">{pretty(manifest?.manifest || {})}</pre>
            </div>
          </section>

          <aside className="rounded-2xl border border-[#dbe3ec] bg-white p-4">
            <h2 className="text-sm font-semibold uppercase tracking-[0.11em] text-[#3f5b78]">State / Risk / Decision</h2>
            <div className="mt-3 space-y-2 text-sm text-[#143250]">
              <div>
                <strong>state:</strong> {decision?.state_code || "-"}
              </div>
              <div>
                <strong>gate:</strong> {decision?.status_gate || "-"}
              </div>
              <div>
                <strong>approval_required:</strong> {String(decision?.approval_required ?? false)}
              </div>
              <div>
                <strong>risk_flags:</strong> {(decision?.risk_flags || []).join(", ") || "none"}
              </div>
            </div>
            <pre className="mt-3 max-h-[360px] overflow-auto rounded-lg border border-[#dbe3ec] bg-[#f8fbff] p-2 text-xs text-[#18314b]">
              {pretty(decision?.decision_json || {})}
            </pre>
          </aside>
        </div>
      </div>
    </AppShell>
  );
}
