"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { ensureSession } from "@/lib/sessionStore";
import { resolveFileAppPath } from "@/lib/workspace-routing";
import { uploadDirect } from "@/services/api";

export default function UploadPage() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleFile(file: File) {
    setBusy(true);
    setError(null);

    try {
      const workspace = ensureSession();
      const uploaded = await uploadDirect(file);
      const route = resolveFileAppPath(
        workspace.id,
        { original_filename: file.name, content_type: file.type },
        uploaded.file_id
      );
      router.push(route.href);
    } catch (err) {
      setError(err instanceof Error ? err.message : "The upload could not be completed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="workspace-section">
      <div className="hero-card">
        <div className="eyebrow">Upload entry</div>
        <h1 className="display-title">Start with the file. Let the suite choose the right application.</h1>
        <p className="lede">This public surface creates or reuses a workspace and routes the file into the focused app.</p>
        <div className="hero-actions">
          <button className="button button--primary" type="button" onClick={() => inputRef.current?.click()}>
            {busy ? "Uploading..." : "Choose file"}
          </button>
        </div>
        {error ? <p className="page-copy" style={{ color: "#b42318" }}>{error}</p> : null}
        <input
          ref={inputRef}
          className="hidden-input"
          type="file"
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) void handleFile(file);
            event.currentTarget.value = "";
          }}
        />
      </div>
    </section>
  );
}
