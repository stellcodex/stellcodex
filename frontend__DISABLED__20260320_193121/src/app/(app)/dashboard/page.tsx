"use client";

import { ChangeEvent, useEffect, useRef, useState } from "react";

type UnknownRecord = Record<string, unknown>;

function normalizeArray(payload: unknown): UnknownRecord[] {
  if (Array.isArray(payload)) {
    return payload.filter(
      (item): item is UnknownRecord =>
        typeof item === "object" && item !== null && !Array.isArray(item),
    );
  }

  if (payload && typeof payload === "object") {
    const record = payload as Record<string, unknown>;
    const candidate = record.items ?? record.data ?? record.files ?? record.jobs ?? record.results;
    if (Array.isArray(candidate)) {
      return candidate.filter(
        (item): item is UnknownRecord =>
          typeof item === "object" && item !== null && !Array.isArray(item),
      );
    }
  }

  return [];
}

function firstString(record: UnknownRecord, keys: string[]): string {
  for (const key of keys) {
    const value = record[key];
    if (typeof value === "string" && value.trim()) {
      return value;
    }
    if (typeof value === "number") {
      return String(value);
    }
  }

  return "Unknown";
}

function prettyTimestamp(value: unknown): string | null {
  if (typeof value !== "string" && typeof value !== "number") {
    return null;
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return null;
  }

  return date.toLocaleString();
}

async function readJson(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) {
    return null;
  }

  return response.json();
}

export default function DashboardPage() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<UnknownRecord[]>([]);
  const [jobs, setJobs] = useState<UnknownRecord[]>([]);
  const [loadingFiles, setLoadingFiles] = useState(true);
  const [loadingJobs, setLoadingJobs] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadFiles() {
    setLoadingFiles(true);
    try {
      const response = await fetch("/api/v1/files", { cache: "no-store" });
      if (!response.ok) {
        throw new Error(`Files request failed with ${response.status}`);
      }

      const payload = await readJson(response);
      setFiles(normalizeArray(payload));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load files.");
      setFiles([]);
    } finally {
      setLoadingFiles(false);
    }
  }

  async function loadJobs() {
    setLoadingJobs(true);
    try {
      const response = await fetch("/api/v1/jobs", { cache: "no-store" });
      if (!response.ok) {
        throw new Error(`Jobs request failed with ${response.status}`);
      }

      const payload = await readJson(response);
      setJobs(normalizeArray(payload));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load jobs.");
      setJobs([]);
    } finally {
      setLoadingJobs(false);
    }
  }

  useEffect(() => {
    void Promise.all([loadFiles(), loadJobs()]);
  }, []);

  async function uploadWithField(file: File, fieldName: string) {
    const formData = new FormData();
    formData.append(fieldName, file);

    return fetch("/api/v1/files", {
      method: "POST",
      body: formData,
    });
  }

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const selectedFile = event.target.files?.[0];
    if (!selectedFile) {
      return;
    }

    setUploading(true);
    setError(null);

    try {
      let response = await uploadWithField(selectedFile, "file");
      if (!response.ok) {
        response = await uploadWithField(selectedFile, "files");
      }

      if (!response.ok) {
        throw new Error(`Upload failed with ${response.status}`);
      }

      await Promise.all([loadFiles(), loadJobs()]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to upload file.");
    } finally {
      event.target.value = "";
      setUploading(false);
    }
  }

  return (
    <main
      style={{
        minHeight: "100vh",
        background: "linear-gradient(180deg, #f7f7f5 0%, #ece8df 100%)",
        color: "#171717",
        padding: "32px 20px 48px",
      }}
    >
      <div
        style={{
          margin: "0 auto",
          maxWidth: 1040,
          display: "grid",
          gap: 24,
        }}
      >
        <section
          style={{
            backgroundColor: "#fffdf8",
            border: "1px solid #d7cfbf",
            borderRadius: 20,
            padding: 24,
            boxShadow: "0 20px 60px rgba(48, 39, 23, 0.08)",
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              gap: 16,
              flexWrap: "wrap",
            }}
          >
            <div>
              <p
                style={{
                  margin: 0,
                  fontSize: 12,
                  letterSpacing: "0.16em",
                  textTransform: "uppercase",
                  color: "#7c6e56",
                }}
              >
                Dashboard
              </p>
              <h1
                style={{
                  margin: "8px 0 0",
                  fontSize: "clamp(2rem, 4vw, 3rem)",
                  lineHeight: 1,
                }}
              >
                Files and jobs
              </h1>
            </div>

            <div>
              <input
                ref={fileInputRef}
                type="file"
                onChange={handleFileChange}
                style={{ display: "none" }}
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
                style={{
                  border: "none",
                  borderRadius: 999,
                  backgroundColor: uploading ? "#a8997c" : "#1f5f4a",
                  color: "#fff",
                  cursor: uploading ? "not-allowed" : "pointer",
                  fontSize: 15,
                  fontWeight: 600,
                  padding: "14px 22px",
                }}
              >
                {uploading ? "Uploading..." : "Upload File"}
              </button>
            </div>
          </div>

          {error ? (
            <p
              style={{
                margin: "16px 0 0",
                color: "#9f2d20",
                fontSize: 14,
              }}
            >
              {error}
            </p>
          ) : null}
        </section>

        <div
          style={{
            display: "grid",
            gap: 24,
            gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
          }}
        >
          <section
            style={{
              backgroundColor: "#fff",
              border: "1px solid #ddd3c2",
              borderRadius: 20,
              padding: 24,
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                gap: 12,
                marginBottom: 16,
              }}
            >
              <h2 style={{ margin: 0, fontSize: 22 }}>Recent files</h2>
              <button
                type="button"
                onClick={() => void loadFiles()}
                style={{
                  background: "transparent",
                  border: "1px solid #c8bda7",
                  borderRadius: 999,
                  padding: "8px 12px",
                  cursor: "pointer",
                }}
              >
                Refresh
              </button>
            </div>

            {loadingFiles ? (
              <p style={{ margin: 0, color: "#6a6256" }}>Loading files...</p>
            ) : files.length === 0 ? (
              <p style={{ margin: 0, color: "#6a6256" }}>No files found.</p>
            ) : (
              <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "grid", gap: 12 }}>
                {files.map((file, index) => {
                  const label = firstString(file, [
                    "name",
                    "filename",
                    "originalName",
                    "title",
                    "id",
                  ]);
                  const sublabel =
                    prettyTimestamp(
                      file.updatedAt ?? file.createdAt ?? file.uploadedAt ?? file.timestamp,
                    ) ?? firstString(file, ["status", "type", "contentType", "mimeType"]);

                  return (
                    <li
                      key={`${label}-${index}`}
                      style={{
                        border: "1px solid #ece4d5",
                        borderRadius: 16,
                        padding: 14,
                        backgroundColor: "#fcfaf5",
                      }}
                    >
                      <p style={{ margin: 0, fontWeight: 600 }}>{label}</p>
                      <p style={{ margin: "6px 0 0", fontSize: 14, color: "#6a6256" }}>
                        {sublabel}
                      </p>
                    </li>
                  );
                })}
              </ul>
            )}
          </section>

          <section
            style={{
              backgroundColor: "#fff",
              border: "1px solid #ddd3c2",
              borderRadius: 20,
              padding: 24,
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                gap: 12,
                marginBottom: 16,
              }}
            >
              <h2 style={{ margin: 0, fontSize: 22 }}>Recent jobs</h2>
              <button
                type="button"
                onClick={() => void loadJobs()}
                style={{
                  background: "transparent",
                  border: "1px solid #c8bda7",
                  borderRadius: 999,
                  padding: "8px 12px",
                  cursor: "pointer",
                }}
              >
                Refresh
              </button>
            </div>

            {loadingJobs ? (
              <p style={{ margin: 0, color: "#6a6256" }}>Loading jobs...</p>
            ) : jobs.length === 0 ? (
              <p style={{ margin: 0, color: "#6a6256" }}>No jobs found.</p>
            ) : (
              <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "grid", gap: 12 }}>
                {jobs.map((job, index) => {
                  const label = firstString(job, ["name", "type", "title", "id"]);
                  const status = firstString(job, ["status", "state", "phase"]);
                  const timestamp = prettyTimestamp(
                    job.updatedAt ?? job.createdAt ?? job.startedAt ?? job.timestamp,
                  );

                  return (
                    <li
                      key={`${label}-${index}`}
                      style={{
                        border: "1px solid #ece4d5",
                        borderRadius: 16,
                        padding: 14,
                        backgroundColor: "#fcfaf5",
                      }}
                    >
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          gap: 12,
                          alignItems: "center",
                        }}
                      >
                        <p style={{ margin: 0, fontWeight: 600 }}>{label}</p>
                        <span
                          style={{
                            backgroundColor: "#efe7d7",
                            borderRadius: 999,
                            color: "#604f2c",
                            fontSize: 12,
                            fontWeight: 700,
                            padding: "5px 10px",
                            textTransform: "uppercase",
                          }}
                        >
                          {status}
                        </span>
                      </div>
                      <p style={{ margin: "6px 0 0", fontSize: 14, color: "#6a6256" }}>
                        {timestamp ?? "No timestamp"}
                      </p>
                    </li>
                  );
                })}
              </ul>
            )}
          </section>
        </div>
      </div>
    </main>
  );
}
