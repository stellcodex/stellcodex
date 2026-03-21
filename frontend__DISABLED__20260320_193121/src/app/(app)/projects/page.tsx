"use client";

import { useEffect, useState } from "react";

type ProjectRecord = Record<string, unknown>;

function normalizeProjects(payload: unknown): ProjectRecord[] {
  if (Array.isArray(payload)) {
    return payload.filter(
      (item): item is ProjectRecord =>
        typeof item === "object" && item !== null && !Array.isArray(item),
    );
  }

  if (payload && typeof payload === "object") {
    const record = payload as Record<string, unknown>;
    const candidate = record.items ?? record.data ?? record.projects ?? record.results;
    if (Array.isArray(candidate)) {
      return candidate.filter(
        (item): item is ProjectRecord =>
          typeof item === "object" && item !== null && !Array.isArray(item),
      );
    }
  }

  return [];
}

function pickValue(project: ProjectRecord, keys: string[]): string {
  for (const key of keys) {
    const value = project[key];
    if (typeof value === "string" && value.trim()) {
      return value;
    }
    if (typeof value === "number") {
      return String(value);
    }
  }

  return "Unknown";
}

async function readJson(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) {
    return null;
  }

  return response.json();
}

export default function ProjectsPage() {
  const [projects, setProjects] = useState<ProjectRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadProjects() {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch("/api/v1/projects", { cache: "no-store" });
        if (!response.ok) {
          throw new Error(`Projects request failed with ${response.status}`);
        }

        const payload = await readJson(response);
        setProjects(normalizeProjects(payload));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load projects.");
        setProjects([]);
      } finally {
        setLoading(false);
      }
    }

    void loadProjects();
  }, []);

  return (
    <main
      style={{
        minHeight: "100vh",
        background: "#f5f1e8",
        color: "#1b1a17",
        padding: "32px 20px 48px",
      }}
    >
      <div
        style={{
          margin: "0 auto",
          maxWidth: 960,
          display: "grid",
          gap: 20,
        }}
      >
        <header
          style={{
            background: "#fffdf8",
            border: "1px solid #ddd3c2",
            borderRadius: 20,
            padding: 24,
          }}
        >
          <p
            style={{
              margin: 0,
              fontSize: 12,
              letterSpacing: "0.14em",
              textTransform: "uppercase",
              color: "#7b6b51",
            }}
          >
            Projects
          </p>
          <h1 style={{ margin: "8px 0 0", fontSize: "clamp(2rem, 4vw, 3rem)", lineHeight: 1 }}>
            Project list
          </h1>
        </header>

        <section
          style={{
            background: "#fff",
            border: "1px solid #ddd3c2",
            borderRadius: 20,
            padding: 24,
          }}
        >
          {loading ? (
            <p style={{ margin: 0, color: "#6a6256" }}>Loading projects...</p>
          ) : error ? (
            <p style={{ margin: 0, color: "#9f2d20" }}>{error}</p>
          ) : projects.length === 0 ? (
            <p style={{ margin: 0, color: "#6a6256" }}>No projects found.</p>
          ) : (
            <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "grid", gap: 12 }}>
              {projects.map((project, index) => {
                const id = pickValue(project, ["id", "projectId"]);
                const name = pickValue(project, ["name", "title"]);
                const status = pickValue(project, ["status", "state", "phase"]);

                return (
                  <li
                    key={`${id}-${index}`}
                    style={{
                      border: "1px solid #ece4d5",
                      borderRadius: 16,
                      padding: 16,
                      background: "#fcfaf5",
                    }}
                  >
                    <p style={{ margin: 0, fontSize: 14, color: "#7b6b51" }}>ID: {id}</p>
                    <p style={{ margin: "6px 0 0", fontSize: 18, fontWeight: 600 }}>{name}</p>
                    <p style={{ margin: "6px 0 0", color: "#6a6256" }}>Status: {status}</p>
                  </li>
                );
              })}
            </ul>
          )}
        </section>
      </div>
    </main>
  );
}
