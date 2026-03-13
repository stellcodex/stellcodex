"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { createShare, getFile, getFileStatus, type FileItem } from "@/services/api";

type ViewerState = {
  file: FileItem | null;
  previewUrl: string | null;
  status: string | null;
  shareToken: string | null;
  error: string | null;
};

export default function StandaloneViewerPage({
  params,
}: {
  params: Promise<{ scx_id: string }>;
}) {
  const [fileId, setFileId] = useState("");
  const [state, setState] = useState<ViewerState>({
    file: null,
    previewUrl: null,
    status: null,
    shareToken: null,
    error: null,
  });
  const [busy, setBusy] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function init() {
      const resolved = await params;
      if (!active) return;
      setFileId(resolved.scx_id);
    }

    void init();

    return () => {
      active = false;
    };
  }, [params]);

  useEffect(() => {
    if (!fileId) return;
    let active = true;

    async function load() {
      try {
        const [file, status] = await Promise.all([getFile(fileId), getFileStatus(fileId)]);
        if (!active) return;
        setState({
          file,
          previewUrl: file.preview_url || file.original_url || file.gltf_url || null,
          status: status?.state || file.status || null,
          shareToken: null,
          error: null,
        });
      } catch (err) {
        if (!active) return;
        setState((current) => ({
          ...current,
          error: err instanceof Error ? err.message : "The file viewer could not be opened.",
        }));
      }
    }

    void load();

    return () => {
      active = false;
    };
  }, [fileId]);

  async function handleShare() {
    if (!fileId) return;
    setBusy("share");

    try {
      const share = await createShare(fileId, 7 * 24 * 60 * 60);
      setState((current) => ({ ...current, shareToken: share.token }));
    } catch (err) {
      setState((current) => ({
        ...current,
        error: err instanceof Error ? err.message : "A share link could not be created.",
      }));
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="viewer-shell">
      <section className="viewer-frame">
        <div className="viewer-card">
          <div className="eyebrow">Viewer</div>
          <h1 className="page-title">{state.file?.original_name || "Loading file"}</h1>
          <p className="page-copy">
            Standalone review stays focused. Files, projects, and apps remain in the suite shell.
          </p>
          <div className="hero-actions">
            <Link className="button button--ghost" href="/">
              Suite home
            </Link>
            <button className="button button--primary" type="button" onClick={() => void handleShare()}>
              {busy === "share" ? "Creating share..." : "Create share"}
            </button>
          </div>
          {state.shareToken ? (
            <p className="page-copy" style={{ marginTop: "1rem" }}>
              Public share: <Link href={`/s/${state.shareToken}`}>/s/{state.shareToken}</Link>
            </p>
          ) : null}
          {state.error ? <p className="page-copy" style={{ color: "#b42318" }}>{state.error}</p> : null}
        </div>

        <div className="viewer-preview">
          {state.previewUrl ? (
            state.previewUrl.match(/\.(png|jpg|jpeg|gif|webp)$/i) ? (
              <img alt={state.file?.original_name || "Preview"} src={state.previewUrl} />
            ) : (
              <iframe src={state.previewUrl} title={state.file?.original_name || "Viewer preview"} />
            )
          ) : (
            <div className="viewer-card" style={{ minHeight: "420px", display: "grid", placeItems: "center" }}>
              <p className="page-copy">No inline preview is ready yet. Use the source download when processing finishes.</p>
            </div>
          )}
        </div>

        <div className="panel-grid">
          <div className="viewer-card">
            <h3>File state</h3>
            <div className="list-item-meta">
              <span className="status-chip">{state.status || "processing"}</span>
              <span>{state.file?.content_type || "unknown content type"}</span>
            </div>
          </div>
          <div className="viewer-card">
            <h3>Source</h3>
            {state.file?.original_url ? (
              <a className="button button--ghost" href={state.file.original_url} target="_blank" rel="noreferrer">
                Download source
              </a>
            ) : (
              <p className="page-copy">Source download is not published yet.</p>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
