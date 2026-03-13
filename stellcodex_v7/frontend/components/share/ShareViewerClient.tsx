"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ApiHttpError, resolveShare, type ShareResolveResult } from "@/services/api";

export function ShareViewerClient({ token }: { token: string }) {
  const [data, setData] = useState<ShareResolveResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const next = await resolveShare(token);
        if (active) setData(next);
      } catch (err) {
        if (!active) return;
        if (err instanceof ApiHttpError) {
          setError(err.message);
          return;
        }
        setError("The share link could not be opened.");
      }
    }

    void load();

    return () => {
      active = false;
    };
  }, [token]);

  return (
    <div className="viewer-shell">
      <section className="viewer-frame">
        <div className="viewer-card">
          <div className="eyebrow">Public share</div>
          <h1 className="page-title">Shared file access</h1>
          <p className="page-copy">
            Open the shared viewer, verify permissions, and continue into the main workspace if needed.
          </p>
        </div>

        {error ? (
          <div className="viewer-card">
            <h3>Share unavailable</h3>
            <p className="page-copy">{error}</p>
          </div>
        ) : null}

        {data ? (
          <div className="panel-grid">
            <div className="viewer-card">
              <h3>{data.original_filename}</h3>
              <div className="list-item-meta">
                <span className="status-chip">{data.status}</span>
                <span>{data.permission}</span>
                <span>{data.content_type}</span>
              </div>
              <div className="hero-actions">
                <Link className="button button--primary" href={`/view/${data.file_id}`}>
                  Open viewer
                </Link>
                {data.original_url ? (
                  <a className="button button--ghost" href={data.original_url} target="_blank" rel="noreferrer">
                    Download source
                  </a>
                ) : null}
              </div>
            </div>
            <div className="viewer-card">
              <h3>Permissions</h3>
              <p className="page-copy">
                View: {data.can_view ? "allowed" : "blocked"}<br />
                Download: {data.can_download ? "allowed" : "blocked"}
              </p>
              <p className="muted">This surface stays intentionally simple and only exposes valid actions.</p>
            </div>
          </div>
        ) : !error ? (
          <div className="viewer-card">
            <p className="page-copy">Resolving the share link.</p>
          </div>
        ) : null}
      </section>
    </div>
  );
}
