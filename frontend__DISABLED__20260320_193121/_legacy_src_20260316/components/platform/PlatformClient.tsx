"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useUser } from "@/context/UserContext";
import { getHomePlatformApps, getPlatformApp, type PlatformAppId, type PlatformSurface } from "@/data/platformCatalog";
import {
  getMarketplaceIntegration,
  normalizeMarketplaceCategory,
  resolveMarketplaceCoreAppId,
  summarizeMarketplaceCapabilities,
} from "@/data/platformMarketplace";
import { loadLatestRecords, saveRecordFile, type PersistedRecord } from "@/lib/fileRecords";
import {
  ensureSession,
  loadSessions,
  newSession,
  saveActiveSessionId,
  saveSessions,
  type WorkspaceSession,
} from "@/lib/sessionStore";
import {
  buildStandaloneViewerPath,
  buildWorkspaceAppPath,
  buildWorkspaceOpenPath,
  buildWorkspacePath,
  buildWorkspaceProjectPath,
  classifyWorkspaceApp,
  extractWorkspaceId,
  resolveFileAppPath,
  resolveWorkspaceHref,
} from "@/lib/workspace-routing";
import {
  createProject,
  createShare,
  enqueueConvert,
  enqueueMesh2d3d,
  enqueueMoldcodesExport,
  fetchAuthedBlobUrl,
  getAppManifest,
  getFile,
  getFileStatus,
  getJob,
  getLibraryFeed,
  getProject,
  listAppsCatalog,
  listFiles,
  listProjects,
  publishLibraryItem,
  type AppManifestResponse,
  type AppsCatalogItem,
  type FileDetail,
  type FileItem,
  type JobStatus,
  type LibraryItem,
  type ProjectSummary,
  uploadDirect,
} from "@/services/api";
import { PlatformLayout } from "./PlatformLayout";

type PlatformView = "home" | "apps" | "app" | "projects" | "project" | "files" | "library" | "settings" | "admin" | "viewer";

type PlatformClientProps = {
  view: PlatformView;
  appId?: string;
  projectId?: string;
  fileId?: string;
};

type RecordField = {
  key: string;
  label: string;
  type: "text" | "textarea" | "number" | "date" | "select";
  options?: string[];
  placeholder?: string;
};

type WorkspaceData = {
  projects: ProjectSummary[];
  files: FileItem[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
};

type PublishDocument = {
  filename: string;
  title: string;
  html: string;
  expiresInSeconds?: number;
};
const SOCIAL_OAUTH_BLOCKERS = ["META_APP_ID", "META_APP_SECRET"] as const;
const HOME_FOCUS_APP_IDS: PlatformAppId[] = ["viewer3d", "viewer2d", "docviewer", "drive", "projects", "applications"];
const CATALOG_FOCUS_APP_IDS: PlatformAppId[] = ["viewer3d", "viewer2d", "docviewer", "drive", "projects", "moldcodes"];
const SUITE_PLAN_ROWS = [
  {
    name: "Free",
    headline: "Start fast",
    description: "Core upload routing, viewer access, and the shared STELLCODEX shell.",
  },
  {
    name: "Plus",
    headline: "Go deeper",
    description: "Expanded app usage, longer workflows, and more engineering runtime access.",
  },
  {
    name: "Pro",
    headline: "Run the suite",
    description: "Team workflows, advanced automation, and the full STELLCODEX operating surface.",
  },
] as const;

type MoldFamilyConfig = {
  label: string;
  minWidth: number;
  maxWidth: number;
  minHeight: number;
  maxHeight: number;
  minThickness: number;
  maxThickness: number;
};

const MOLD_CATALOG = {
  plates: {
    label: "Plates / Mold Base",
    families: {
      "base-a": { label: "Base A", minWidth: 80, maxWidth: 800, minHeight: 80, maxHeight: 800, minThickness: 16, maxThickness: 120 },
      "plate-b": { label: "Plate B", minWidth: 50, maxWidth: 600, minHeight: 50, maxHeight: 600, minThickness: 12, maxThickness: 90 },
    },
  },
  guiding: {
    label: "Guiding",
    families: {
      "guide-pin": { label: "Guide Pin", minWidth: 8, maxWidth: 40, minHeight: 40, maxHeight: 220, minThickness: 8, maxThickness: 40 },
      "guide-bush": { label: "Guide Bush", minWidth: 12, maxWidth: 50, minHeight: 18, maxHeight: 120, minThickness: 8, maxThickness: 40 },
    },
  },
  ejectors: {
    label: "Ejectors",
    families: {
      "ejector-pin": { label: "Ejector Pin", minWidth: 2, maxWidth: 20, minHeight: 40, maxHeight: 300, minThickness: 2, maxThickness: 20 },
      "sleeve-ejector": { label: "Sleeve Ejector", minWidth: 6, maxWidth: 36, minHeight: 35, maxHeight: 260, minThickness: 4, maxThickness: 30 },
    },
  },
} as const;

function getMoldFamilyConfig(category: keyof typeof MOLD_CATALOG, family: string): MoldFamilyConfig {
  const families = MOLD_CATALOG[category].families as Record<string, MoldFamilyConfig>;
  return families[family] || Object.values(families)[0];
}

function formatDate(value?: string | null) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function titleCase(input: string) {
  return input
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function escapeHtml(value: unknown) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function slugify(value: unknown, fallback: string) {
  const normalized = String(value ?? "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return normalized || fallback;
}

function richTextToHtml(value: unknown) {
  return escapeHtml(value).replace(/\n/g, "<br />");
}

function buildPublishedPage(kind: "webbuilder" | "cms", payload: Record<string, unknown>): PublishDocument {
  const title = String(payload.title || (kind === "webbuilder" ? "Landing Page" : "Knowledge Article")).trim() || "Published Page";
  const slug = slugify(payload.slug || title, kind === "webbuilder" ? "landing-page" : "knowledge-article");
  const headline = String(payload.headline || title).trim() || title;
  const ctaLabel = String(payload.ctaLabel || "Contact sales").trim() || "Contact sales";
  const body = richTextToHtml(payload.body || "");
  const status = escapeHtml(payload.status || "draft");
  const publishedAt = new Date().toLocaleString("en-US");

  if (kind === "webbuilder") {
    return {
      filename: `${slug}.html`,
      title,
      expiresInSeconds: 30 * 24 * 60 * 60,
      html: `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>${escapeHtml(title)}</title>
  <style>
    :root { color-scheme: dark; }
    * { box-sizing: border-box; }
    body { margin: 0; font-family: "Segoe UI", sans-serif; background: radial-gradient(circle at top, #132238, #050816 72%); color: #f8fafc; }
    .shell { min-height: 100vh; display: grid; place-items: center; padding: 48px 20px; }
    .card { width: min(920px, 100%); border: 1px solid rgba(148,163,184,0.22); border-radius: 28px; background: rgba(15,23,42,0.88); padding: 48px; box-shadow: 0 32px 80px rgba(2,6,23,0.45); }
    .eyebrow { text-transform: uppercase; letter-spacing: 0.18em; color: #7dd3fc; font-size: 12px; }
    h1 { margin: 18px 0 0; font-size: clamp(40px, 7vw, 72px); line-height: 0.95; }
    .body { margin-top: 20px; max-width: 700px; color: #cbd5e1; font-size: 18px; line-height: 1.7; }
    .cta { display: inline-block; margin-top: 28px; padding: 14px 22px; border-radius: 999px; background: #f8fafc; color: #020617; text-decoration: none; font-weight: 700; }
    .meta { margin-top: 28px; color: #94a3b8; font-size: 13px; }
  </style>
</head>
<body>
  <main class="shell">
    <section class="card">
      <div class="eyebrow">STELLCODEX Web Builder Publish</div>
      <h1>${escapeHtml(headline)}</h1>
      <div class="body">${body || "Published from the STELLCODEX Web Builder runner."}</div>
      <a class="cta" href="#">${escapeHtml(ctaLabel)}</a>
      <div class="meta">Slug: ${escapeHtml(slug)} | Published: ${escapeHtml(publishedAt)}</div>
    </section>
  </main>
</body>
</html>`,
    };
  }

  return {
    filename: `${slug}.html`,
    title,
    expiresInSeconds: 30 * 24 * 60 * 60,
    html: `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>${escapeHtml(title)}</title>
  <style>
    :root { color-scheme: light; }
    * { box-sizing: border-box; }
    body { margin: 0; font-family: Georgia, "Times New Roman", serif; background: #f7f7f5; color: #111827; }
    .shell { min-height: 100vh; padding: 48px 20px 80px; }
    article { width: min(860px, 100%); margin: 0 auto; background: #fff; border-radius: 28px; border: 1px solid #e5e7eb; padding: 56px 48px; box-shadow: 0 24px 60px rgba(15,23,42,0.08); }
    .eyebrow { text-transform: uppercase; letter-spacing: 0.16em; color: #0f766e; font: 600 12px/1.4 "Segoe UI", sans-serif; }
    h1 { margin: 18px 0 0; font-size: clamp(34px, 6vw, 56px); line-height: 1.02; }
    .meta { margin-top: 18px; color: #6b7280; font: 500 14px/1.6 "Segoe UI", sans-serif; }
    .body { margin-top: 28px; font-size: 20px; line-height: 1.8; color: #1f2937; }
  </style>
</head>
<body>
  <main class="shell">
    <article>
      <div class="eyebrow">STELLCODEX CMS Publish</div>
      <h1>${escapeHtml(title)}</h1>
      <div class="meta">Slug: ${escapeHtml(slug)} | Status: ${status} | Published: ${escapeHtml(publishedAt)}</div>
      <div class="body">${body || "Published from the STELLCODEX CMS runner."}</div>
    </article>
  </main>
</body>
</html>`,
  };
}

function summarizeResult(value?: string | null) {
  if (!value) return null;
  try {
    const normalized = value.replace(/'/g, '"');
    return JSON.parse(normalized) as Record<string, unknown>;
  } catch {
    return null;
  }
}

function extractOutputFileId(job?: JobStatus | null) {
  if (!job?.result) return null;
  const parsed = summarizeResult(job.result);
  if (parsed && typeof parsed.file_id === "string") return parsed.file_id;
  const matched = job.result.match(/file_id['"]?\s*[:=]\s*['"]([^'"]+)['"]/);
  return matched ? matched[1] : null;
}

function appForFile(file: { original_filename?: string | null; content_type?: string | null }) {
  return classifyWorkspaceApp(file);
}

function fileRouteCopy(appId: ReturnType<typeof classifyWorkspaceApp>) {
  if (appId === "viewer2d") {
    return {
      label: "2D Drawings",
      description: "DXF and flat technical files open in the 2D drawing workspace.",
    };
  }
  if (appId === "docviewer") {
    return {
      label: "Documents",
      description: "PDF, image, and office documents open in the document workspace.",
    };
  }
  return {
    label: "3D Review",
    description: "3D models and assemblies open in the 3D review workspace.",
  };
}

function resolveUploadedFileDestination(
  workspaceId: string | null,
  file: { original_filename?: string | null; content_type?: string | null },
  fileId: string
) {
  const destination = resolveFileAppPath(workspaceId, file, fileId);
  return {
    ...destination,
    ...fileRouteCopy(destination.appId),
  };
}

function viewerSurfaceContent(surface: PlatformSurface) {
  if (surface === "viewer2d") {
    return {
      label: "2D Drawing Workspace",
      description: "Focused on technical drawings, DXF review, layers, and clean document handoff.",
      stageTitle: "2D Drawing Stage",
      stageDescription: "Use this surface for drawings and flat technical layouts. Viewer actions stay limited to the essentials.",
      emptyTitle: "Select a drawing file",
      emptyDescription: "Choose a DXF or drawing-oriented file to open the dedicated 2D review surface.",
      tips: ["Drawing-first layout", "DXF-ready file routing", "Minimal review actions"],
    };
  }
  if (surface === "docviewer") {
    return {
      label: "Document Workspace",
      description: "Focused on PDF and document review, file status, and controlled download or share actions.",
      stageTitle: "Document Stage",
      stageDescription: "Use this surface for project documents, PDFs, images, and office artifacts.",
      emptyTitle: "Select a document file",
      emptyDescription: "Choose a PDF or document artifact to open the document review surface.",
      tips: ["Document-first layout", "Clear metadata and status", "No viewer tool clutter"],
    };
  }
  return {
    label: "3D Review Workspace",
    description: "Focused on part and assembly review, viewer status, and direct handoff into the deep-link viewer.",
    stageTitle: "3D Review Stage",
    stageDescription: "Use this surface for STEP, STL, OBJ, GLB, and other 3D-oriented files.",
    emptyTitle: "Select a 3D file",
    emptyDescription: "Choose a model file to open the dedicated 3D review surface.",
    tips: ["3D-first layout", "Large viewer stage", "Short action rail"],
  };
}

function viewerSurfaceTheme(surface: PlatformSurface) {
  if (surface === "viewer2d") {
    return {
      badge: "2D Drawing",
      stageShell: "border-[#d8e1e8] bg-[#f8fbfd]",
      frameTone: "bg-white",
      sideTitle: "Drawing flow",
      sideDescription: "Layer-focused review for flat technical files.",
      tips: ["Drawing-focused surface", "Flat canvas and clean contrast", "Keep review actions short"],
    };
  }
  if (surface === "docviewer") {
    return {
      badge: "Documents",
      stageShell: "border-[#e5dfd4] bg-[#fbfaf6]",
      frameTone: "bg-[#fbfaf7]",
      sideTitle: "Document flow",
      sideDescription: "Review documents, status, and controlled handoff without viewer clutter.",
      tips: ["Reading-first surface", "Status and download stay visible", "Share actions stay controlled"],
    };
  }
  return {
    badge: "3D Review",
    stageShell: "border-[#d5dee0] bg-[#f4f8f8]",
    frameTone: "bg-[#0b1212]",
    sideTitle: "3D flow",
    sideDescription: "Large stage for model review with short actions on the side.",
    tips: ["Large visual stage", "Direct app handoff", "Short action rail only"],
  };
}

function formatBytes(size?: number | null) {
  if (!size) return "0 B";
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

function resolveAppHref(workspaceId: string | null, appId: string, fileId?: string | null) {
  const platformApp = getPlatformApp(appId);
  if (platformApp) {
    if (fileId && platformApp.route.startsWith("/app/")) {
      return workspaceId ? buildWorkspaceAppPath(workspaceId, appId, fileId) : `${platformApp.route}?file_id=${encodeURIComponent(fileId)}`;
    }
    return resolveWorkspaceHref(workspaceId, platformApp.route);
  }
  if (workspaceId) return buildWorkspaceAppPath(workspaceId, appId, fileId);
  const base = `/app/${encodeURIComponent(appId)}`;
  return fileId ? `${base}?file_id=${encodeURIComponent(fileId)}` : base;
}

function resolveProjectHref(workspaceId: string | null, projectId: string) {
  return workspaceId ? buildWorkspaceProjectPath(workspaceId, projectId) : `/project/${encodeURIComponent(projectId)}`;
}

function resolveFileOpenHref(workspaceId: string | null, fileId: string) {
  return workspaceId ? buildWorkspaceOpenPath(workspaceId, fileId) : buildStandaloneViewerPath(fileId);
}

function useWorkspaceData(): WorkspaceData {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [files, setFiles] = useState<FileItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setLoading(true);
    try {
      const [projectRows, fileRows] = await Promise.all([listProjects(), listFiles()]);
      setProjects(projectRows);
      setFiles(fileRows);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Workspace data could not be loaded.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  return { projects, files, loading, error, refresh };
}

function SectionCard({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-[24px] border border-[#e5e7eb] bg-white p-5 shadow-[0_12px_30px_rgba(15,23,42,0.04)]">
      <div className="mb-4">
        <div className="text-lg font-semibold text-[#111827]">{title}</div>
        {description ? <div className="mt-1 text-sm text-[#6b7280]">{description}</div> : null}
      </div>
      {children}
    </section>
  );
}

function StatusBadge({ label }: { label: string }) {
  const normalized = label.toLowerCase();
  const tone =
    normalized === "ready" || normalized === "finished" || normalized === "ok" || normalized === "enabled" || normalized === "succeeded"
      ? "border-[#b7d9d5] bg-[#eef8f6] text-[#0f766e]"
      : normalized === "failed"
      ? "border-[#f1c9c9] bg-[#fff5f5] text-[#b42318]"
      : "border-[#f3ddaa] bg-[#fff8e8] text-[#7a4b00]";
  return <span className={`rounded-full border px-2.5 py-1 text-xs ${tone}`}>{titleCase(label)}</span>;
}

function EmptyPanel({ title, description }: { title: string; description: string }) {
  return (
    <div className="rounded-[24px] border border-dashed border-[#d7dfde] bg-white p-6 text-sm text-[#4b5563]">
      <div className="font-medium text-[#1f2937]">{title}</div>
      <div className="mt-1">{description}</div>
    </div>
  );
}

function BlockerPanel({
  title,
  description,
  blockerKeys,
}: {
  title: string;
  description: string;
  blockerKeys: readonly string[];
}) {
  return (
    <div className="rounded-[24px] border border-[#f3ddaa] bg-[#fff8e8] p-5 text-sm text-[#7a4b00]">
      <div className="font-semibold text-[#7a4b00]">{title}</div>
      <div className="mt-2 text-[#8a5a10]">{description}</div>
      <div className="mt-4 flex flex-wrap gap-2">
        {blockerKeys.map((key) => (
          <span key={key} className="rounded-full border border-[#f3ddaa] bg-white px-3 py-1 text-xs tracking-[0.14em] text-[#7a4b00]">
            {key}
          </span>
        ))}
      </div>
    </div>
  );
}

function HomeScreen() {
  // The suite home is intentionally simple: one entry surface, then fast handoff into focused apps.
  const router = useRouter();
  const pathname = usePathname();
  const { user } = useUser();
  const [sessions, setSessions] = useState<WorkspaceSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const uploadInputRef = useRef<HTMLInputElement | null>(null);
  const workspaceId = extractWorkspaceId(pathname);
  const workspace = useWorkspaceData();

  useEffect(() => {
    const current = ensureSession(workspaceId || undefined);
    const stored = loadSessions();
    setSessions(stored.length > 0 ? stored : [current]);
    setActiveSessionId(current.id);
  }, [workspaceId]);

  const activeSession = sessions.find((item) => item.id === activeSessionId) || sessions[0] || null;
  const visibleApps = getHomePlatformApps(user.role);
  const focusApps = HOME_FOCUS_APP_IDS
    .map((appId) => visibleApps.find((app) => app.id === appId))
    .filter((app): app is NonNullable<typeof app> => app !== undefined);
  const recentFiles = workspace.files.slice(0, 6);
  const recentProjects = workspace.projects.slice(0, 5);
  function onSelectSession(sessionId: string) {
    setActiveSessionId(sessionId);
    saveActiveSessionId(sessionId);
    router.push(buildWorkspacePath(sessionId));
  }

  function onNewSession() {
    const created = newSession();
    const next = [created, ...sessions];
    saveSessions(next);
    saveActiveSessionId(created.id);
    setSessions(next);
    setActiveSessionId(created.id);
    router.push(buildWorkspacePath(created.id));
  }

  async function onUpload(files: FileList | null) {
    const file = files?.[0];
    if (!file) return;
    setUploading(true);
    setUploadError(null);
    setUploadStatus("Uploading file...");
    try {
      const result = await uploadDirect(file);
      const destination = resolveUploadedFileDestination(
        workspaceId,
        { original_filename: file.name, content_type: file.type || null },
        result.file_id
      );
      setUploadStatus(`Opening ${destination.label}...`);
      router.push(destination.href);
    } catch (err) {
      setUploadStatus(null);
      setUploadError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <PlatformLayout
      title={activeSession?.title || "Workspace"}
      mode="hub"
      sessionState={{ sessions, activeSessionId, onSelectSession, onNewSession }}
    >
      <div className="mx-auto flex w-full max-w-[1480px] flex-col gap-5 px-4 py-5 lg:px-6">
        <section className="rounded-[28px] border border-[#e5e7eb] bg-white p-6 shadow-[0_16px_42px_rgba(15,23,42,0.04)] lg:p-7">
          <input ref={uploadInputRef} type="file" className="hidden" onChange={(event) => void onUpload(event.target.files)} />
          <div className="max-w-3xl">
            <div className="text-[11px] font-semibold uppercase tracking-[0.28em] text-[#6b7280]">Start work</div>
            <div className="mt-3 text-[clamp(2.1rem,4vw,3.8rem)] font-semibold tracking-[-0.04em] text-[#111827]">
              Upload a file or open an app.
            </div>
            <div className="mt-3 text-sm text-[#4b5563]">STELLCODEX routes the file into the correct workspace.</div>
            <div className="mt-6 flex flex-wrap gap-3">
              <button
                type="button"
                onClick={() => uploadInputRef.current?.click()}
                className="rounded-2xl bg-[var(--accent)] px-5 py-3 text-sm font-medium text-white hover:opacity-95"
              >
                {uploading ? "Uploading..." : "Upload file"}
              </button>
              <Link href={resolveWorkspaceHref(workspaceId, "/apps")} className="rounded-2xl border border-[#e5e7eb] px-5 py-3 text-sm text-[#1f2937] hover:bg-[#f8fafc]">
                Open applications
              </Link>
              <button
                type="button"
                onClick={() => document.getElementById("recent-sessions")?.scrollIntoView({ behavior: "smooth", block: "start" })}
                className="rounded-2xl border border-[#e5e7eb] px-5 py-3 text-sm text-[#1f2937] hover:bg-[#f8fafc]"
              >
                Recent sessions
              </button>
            </div>
            {uploadStatus ? <div className="mt-4 text-sm text-[#4b5563]">{uploadStatus}</div> : null}
            {uploadError ? <div className="mt-4 text-sm text-[#b42318]">{uploadError}</div> : null}
            {workspace.error ? <div className="mt-4 text-sm text-[#b42318]">{workspace.error}</div> : null}
          </div>
        </section>

        <div className="grid gap-5 xl:grid-cols-[minmax(0,1.12fr)_360px]">
          <SectionCard title="Recent files" description="Continue from the latest work">
            {workspace.loading ? <div className="text-sm text-[#6b7280]">Loading recent files...</div> : null}
            {!workspace.loading && recentFiles.length === 0 ? (
              <EmptyPanel title="No files yet" description="Upload the first file to start routing." />
            ) : null}
            {!workspace.loading ? (
              <div className="space-y-2">
                {recentFiles.map((file) => {
                  const destination = resolveUploadedFileDestination(
                    workspaceId,
                    { original_filename: file.original_filename, content_type: file.content_type || null },
                    file.file_id
                  );
                  return (
                    <button
                      key={file.file_id}
                      type="button"
                      onClick={() => router.push(destination.href)}
                      className="flex w-full items-center justify-between gap-4 rounded-[18px] border border-[#e5e7eb] bg-[#fcfcfb] px-4 py-3 text-left hover:bg-[#f8fafc]"
                    >
                      <div className="min-w-0 flex-1">
                        <div className="truncate text-sm font-medium text-[#111827]">{file.original_filename}</div>
                        <div className="mt-1 text-xs text-[#6b7280]">
                          {destination.label} • {formatDate(file.created_at)}
                        </div>
                      </div>
                      <StatusBadge label={file.status} />
                    </button>
                  );
                })}
              </div>
            ) : null}
          </SectionCard>

          <div className="space-y-5">
            <div id="recent-sessions">
              <SectionCard title="Recent sessions" description="Jump back into an existing workspace">
                {sessions.length === 0 ? (
                  <EmptyPanel title="No sessions yet" description="A workspace session appears after the first action." />
                ) : (
                  <div className="space-y-2">
                    {sessions.slice(0, 5).map((session) => (
                      <button
                        key={session.id}
                        type="button"
                        onClick={() => onSelectSession(session.id)}
                        className="flex w-full items-center justify-between gap-4 rounded-[18px] border border-[#e5e7eb] bg-[#fcfcfb] px-4 py-3 text-left hover:bg-[#f8fafc]"
                      >
                        <div className="min-w-0 flex-1">
                          <div className="truncate text-sm font-medium text-[#111827]">{session.title}</div>
                          <div className="mt-1 text-xs text-[#6b7280]">{session.id === activeSessionId ? "Current session" : "Saved workspace"}</div>
                        </div>
                        <span className="rounded-full border border-[#e5e7eb] px-2.5 py-1 text-[11px] text-[#6b7280]">Open</span>
                      </button>
                    ))}
                  </div>
                )}
              </SectionCard>
            </div>

            <SectionCard title="Projects" description="Recent project spaces">
              {workspace.loading ? <div className="text-sm text-[#6b7280]">Loading projects...</div> : null}
              {!workspace.loading && recentProjects.length === 0 ? (
                <EmptyPanel title="No projects yet" description="Create a project when files need a long-running home." />
              ) : null}
              {!workspace.loading ? (
                <div className="space-y-2">
                  {recentProjects.map((project) => (
                    <button
                      key={project.id}
                      type="button"
                      onClick={() => router.push(resolveProjectHref(workspaceId, project.id))}
                      className="flex w-full items-center justify-between gap-4 rounded-[18px] border border-[#e5e7eb] bg-[#fcfcfb] px-4 py-3 text-left hover:bg-[#f8fafc]"
                    >
                      <div className="min-w-0 flex-1">
                        <div className="truncate text-sm font-medium text-[#111827]">{project.name}</div>
                        <div className="mt-1 text-xs text-[#6b7280]">{project.file_count} files</div>
                      </div>
                      <span className="rounded-full border border-[#e5e7eb] px-2.5 py-1 text-[11px] text-[#6b7280]">Open</span>
                    </button>
                  ))}
                </div>
              ) : null}
            </SectionCard>
          </div>
        </div>

        <SectionCard title="Applications" description="Core suite entry points">
          <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
            {focusApps.map((app) => (
              <button
                key={app.id}
                type="button"
                onClick={() => router.push(resolveAppHref(workspaceId, app.id))}
                className="flex items-center justify-between rounded-[18px] border border-[#e5e7eb] bg-[#fcfcfb] px-4 py-3 text-left hover:bg-[#f8fafc]"
              >
                <div className="min-w-0">
                  <div className="text-sm font-medium text-[#111827]">{app.name}</div>
                </div>
                <span className="rounded-full border border-[#e5e7eb] px-2.5 py-1 text-[11px] text-[#6b7280]">
                  {app.shortName}
                </span>
              </button>
            ))}
          </div>
        </SectionCard>
      </div>
    </PlatformLayout>
  );
}

function AppsCatalogScreen() {
  const pathname = usePathname();
  const workspaceId = extractWorkspaceId(pathname);
  const [items, setItems] = useState<AppsCatalogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const rows = await listAppsCatalog(true);
        if (!active) return;
        setItems(rows);
        setError(null);
      } catch (err) {
        if (!active) return;
        setError(err instanceof Error ? err.message : "The applications catalog could not be loaded.");
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  const quickAccessIds = new Set(CATALOG_FOCUS_APP_IDS);
  const quickAccessApps = CATALOG_FOCUS_APP_IDS.map((appId) => getPlatformApp(appId)).filter(
    (app): app is NonNullable<ReturnType<typeof getPlatformApp>> => app !== null
  );
  const moduleItems = items.filter((item) => !quickAccessIds.has(item.slug as PlatformAppId));

  const groupedItems = useMemo(() => {
    const groups = new Map<string, AppsCatalogItem[]>();
    for (const item of moduleItems) {
      const key = item.category || "general";
      const list = groups.get(key) || [];
      list.push(item);
      groups.set(key, list);
    }
    return [...groups.entries()]
      .map(([category, rows]) => [
        category,
        rows.sort((a, b) => {
          if (a.enabled !== b.enabled) return Number(b.enabled) - Number(a.enabled);
          return a.name.localeCompare(b.name);
        }),
      ] as const)
      .sort((a, b) => a[0].localeCompare(b[0]));
  }, [moduleItems]);

  const enabledCount = items.filter((item) => item.enabled).length;
  const coreIntegratedCount = items.filter((item) => resolveMarketplaceCoreAppId(item.slug)).length;

  return (
    <PlatformLayout title="Applications" subtitle="One shell. Separate app surfaces.">
      <div className="mx-auto flex w-full max-w-[1500px] flex-col gap-6 px-4 py-6 lg:px-8">
        <SectionCard title="Inventory" description="Registered application surfaces inside the suite.">
          <div className="grid gap-4 md:grid-cols-3">
            <div className="rounded-[24px] border border-[#d7dfde] bg-white p-5">
              <div className="text-xs uppercase tracking-[0.2em] text-[#6b7280]">Apps</div>
              <div className="mt-3 text-3xl font-semibold text-[#111827]">{items.length}</div>
            </div>
            <div className="rounded-[24px] border border-[#d7dfde] bg-white p-5">
              <div className="text-xs uppercase tracking-[0.2em] text-[#6b7280]">Enabled</div>
              <div className="mt-3 text-3xl font-semibold text-[#111827]">{enabledCount}</div>
            </div>
            <div className="rounded-[24px] border border-[#d7dfde] bg-white p-5">
              <div className="text-xs uppercase tracking-[0.2em] text-[#6b7280]">Integrated</div>
              <div className="mt-3 text-3xl font-semibold text-[#111827]">{coreIntegratedCount}</div>
            </div>
          </div>
        </SectionCard>

        <SectionCard title="Core surfaces" description="Start from the main working apps.">
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {quickAccessApps.map((app) => (
              <Link
                key={app.id}
                href={resolveAppHref(workspaceId, app.id)}
                className="rounded-[22px] border border-[#d7dfde] bg-white p-4 transition hover:border-[#bcc9c7] hover:bg-[#f4f7f6]"
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="text-sm font-semibold text-[#111827]">{app.name}</div>
                  <span className="rounded-full border border-[#d7dfde] px-2.5 py-1 text-xs text-[#4b5563]">{app.shortName}</span>
                </div>
                <div className="mt-3 text-sm text-[#4b5563]">{app.summary}</div>
              </Link>
            ))}
          </div>
        </SectionCard>

        {loading ? <SectionCard title="Loading" description="Reading the marketplace registry."><div className="text-sm text-[#4b5563]">Loading application inventory...</div></SectionCard> : null}
        {error ? <SectionCard title="Catalog Error" description="The inventory could not be read."><div className="text-sm text-[#b42318]">{error}</div></SectionCard> : null}

        {groupedItems.map(([category, rows]) => (
          <SectionCard key={category} title={normalizeMarketplaceCategory(category)} description={`${rows.length} app${rows.length === 1 ? "" : "s"}`}>
            <div className="divide-y divide-[#eef2f7]">
              {rows.map((item) => {
                const integration = getMarketplaceIntegration(item);
                return (
                  <Link
                    key={item.slug}
                    href={resolveAppHref(workspaceId, item.slug)}
                    className="flex items-center justify-between gap-4 py-4 first:pt-0 last:pb-0"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <div className="text-sm font-semibold text-[#111827]">{item.name}</div>
                        <StatusBadge label={item.enabled ? "enabled" : "disabled"} />
                        <span className="rounded-full border border-[#d7dfde] px-2.5 py-1 text-xs text-[#4b5563]">{item.tier}</span>
                      </div>
                      <div className="mt-2 text-sm text-[#4b5563]">{integration.headline}</div>
                    </div>
                    <div className="shrink-0 rounded-full border border-[#d7dfde] px-3 py-1 text-xs text-[#4b5563]">
                      Open
                    </div>
                  </Link>
                );
              })}
            </div>
          </SectionCard>
        ))}
      </div>
    </PlatformLayout>
  );
}

function MarketplaceModuleScreen({ slug }: { slug: string }) {
  const pathname = usePathname();
  const workspaceId = extractWorkspaceId(pathname);
  const [catalogItem, setCatalogItem] = useState<AppsCatalogItem | null>(null);
  const [manifest, setManifest] = useState<AppManifestResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const [catalogRows, manifestPayload] = await Promise.all([listAppsCatalog(true), getAppManifest(slug, true)]);
        if (!active) return;
        setCatalogItem(catalogRows.find((item) => item.slug === slug) || null);
        setManifest(manifestPayload);
        setError(null);
      } catch (err) {
        if (!active) return;
        setError(err instanceof Error ? err.message : "The module surface could not be loaded.");
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [slug]);

  const integration = catalogItem ? getMarketplaceIntegration(catalogItem) : null;
  const capabilitySummary = catalogItem ? summarizeMarketplaceCapabilities(catalogItem) : null;
  const declaredRoutes = catalogItem?.routes || [];
  const manifestEndpoints = Array.isArray(manifest?.manifest.api_endpoints) ? (manifest?.manifest.api_endpoints as string[]) : [];
  const workflowFacts = [
    capabilitySummary?.capabilities || "No capability list",
    capabilitySummary?.formats || "No format list",
    integration?.note || "Registered inside the shared suite shell.",
  ];
  const detailRoutes = declaredRoutes.length > 0 ? declaredRoutes : manifestEndpoints;

  return (
    <PlatformLayout title={catalogItem?.name || slug} subtitle="Separate app. Shared platform core.">
      <div className="mx-auto flex w-full max-w-[1480px] flex-col gap-6 px-4 py-6 lg:px-8">
        {loading ? <EmptyPanel title="Loading module" description="Reading the catalog entry and app manifest." /> : null}
        {error ? <EmptyPanel title="Module unavailable" description={error} /> : null}

        {!loading && !error && catalogItem ? (
          <>
            <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
              <SectionCard title={catalogItem.name} description={integration?.headline || "Registered module"}>
                <div className="flex flex-wrap gap-3">
                  <StatusBadge label={catalogItem.enabled ? "enabled" : "disabled"} />
                  <span className="rounded-full border border-[#d7dfde] px-3 py-1 text-xs text-[#4b5563]">{catalogItem.tier}</span>
                  <span className="rounded-full border border-[#d7dfde] px-3 py-1 text-xs text-[#4b5563]">{normalizeMarketplaceCategory(catalogItem.category)}</span>
                </div>
                <div className="mt-5 flex flex-wrap gap-3">
                  {integration?.coreAppId ? (
                    <Link href={resolveAppHref(workspaceId, integration.coreAppId)} className="rounded-2xl bg-[#0f766e] px-5 py-3 text-sm font-medium text-white hover:bg-[#0c5f59]">
                      Open app
                    </Link>
                  ) : (
                    <Link href={resolveAppHref(workspaceId, catalogItem.slug)} className="rounded-2xl bg-[#0f766e] px-5 py-3 text-sm font-medium text-white hover:bg-[#0c5f59]">
                      Open module
                    </Link>
                  )}
                  <Link href={resolveWorkspaceHref(workspaceId, "/apps")} className="rounded-2xl border border-[#d7dfde] px-5 py-3 text-sm text-[#1f2937] hover:bg-[#f4f7f6]">
                    Back to applications
                  </Link>
                </div>
              </SectionCard>

              <SectionCard title="Supported formats" description="What this module accepts">
                <div className="flex flex-wrap gap-2">
                  {(catalogItem.supported_formats.length > 0 ? catalogItem.supported_formats : ["No explicit format list"]).map((format) => (
                    <span key={format} className="rounded-full border border-[#d7dfde] px-3 py-1 text-xs text-[#4b5563]">
                      {format}
                    </span>
                  ))}
                </div>
              </SectionCard>
            </div>

            <div className="grid gap-6 lg:grid-cols-2">
              <SectionCard title="Workflow" description="Simple module summary">
                <div className="space-y-2">
                  {workflowFacts.map((fact) => (
                    <div key={fact} className="rounded-[18px] border border-[#d7dfde] bg-white px-4 py-3 text-sm text-[#4b5563]">
                      {fact}
                    </div>
                  ))}
                </div>
              </SectionCard>

              <SectionCard title="Registered routes" description="Available entry points in the shared suite">
                <div className="space-y-2 text-sm text-[#4b5563]">
                  {detailRoutes.length > 0 ? detailRoutes.map((route) => <div key={route}>{route}</div>) : <div>No extra route list.</div>}
                </div>
              </SectionCard>
            </div>
          </>
        ) : null}
      </div>
    </PlatformLayout>
  );
}

function ProjectsScreen() {
  const workspaceId = extractWorkspaceId(usePathname());
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    try {
      const rows = await listProjects();
      setProjects(rows);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Projects could not be loaded.");
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function onCreate() {
    if (!name.trim()) return;
    setBusy(true);
    try {
      const row = await createProject(name.trim());
      setProjects((prev) => [row, ...prev.filter((item) => item.id !== row.id)]);
      setName("");
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "The project could not be created.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <PlatformLayout title="Projects" subtitle="Create and open project spaces">
      <div className="mx-auto flex w-full max-w-[1320px] flex-col gap-6 px-4 py-6 lg:px-8">
        <section className="rounded-[28px] border border-[#e5e7eb] bg-white p-6 shadow-[0_16px_42px_rgba(15,23,42,0.04)]">
          <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_240px]">
            <div>
              <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#6b7280]">New project</div>
              <div className="mt-3 text-3xl font-semibold tracking-[-0.04em] text-[#111827]">Create a project and keep related files together.</div>
              <div className="mt-5 flex flex-col gap-3 md:flex-row">
                <input
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  placeholder="Injection tooling package"
                  className="h-12 flex-1 rounded-2xl border border-[#d7dfde] bg-white px-4 text-sm text-[#111827] outline-none placeholder:text-[#111827]/30"
                />
                <button
                  type="button"
                  onClick={onCreate}
                  disabled={busy}
                  className="h-12 rounded-2xl bg-[var(--accent)] px-5 text-sm font-medium text-white hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {busy ? "Creating..." : "Create project"}
                </button>
              </div>
              {error ? <div className="mt-3 text-sm text-[#b42318]">{error}</div> : null}
            </div>

            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
              <div className="rounded-[20px] border border-[#e5e7eb] bg-[#fcfcfb] p-4">
                <div className="text-xs uppercase tracking-[0.18em] text-[#6b7280]">Projects</div>
                <div className="mt-2 text-2xl font-semibold text-[#111827]">{projects.length}</div>
              </div>
              <div className="rounded-[20px] border border-[#e5e7eb] bg-[#fcfcfb] p-4">
                <div className="text-xs uppercase tracking-[0.18em] text-[#6b7280]">Files</div>
                <div className="mt-2 text-2xl font-semibold text-[#111827]">{projects.reduce((sum, project) => sum + (project.file_count || 0), 0)}</div>
              </div>
            </div>
          </div>
        </section>

        <SectionCard title="Project list" description="Open an existing project">
          <div className="divide-y divide-[#eef2f7]">
            {projects.map((project) => (
              <Link
                key={project.id}
                href={resolveProjectHref(workspaceId, project.id)}
                className="flex items-center justify-between gap-4 py-4 first:pt-0 last:pb-0"
              >
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm font-semibold text-[#111827]">{project.name}</div>
                  <div className="mt-1 text-xs text-[#6b7280]">Updated {formatDate(project.updated_at)}</div>
                </div>
                <div className="rounded-full border border-[#d7dfde] px-3 py-1 text-xs text-[#4b5563]">{project.file_count} files</div>
              </Link>
            ))}
            {projects.length === 0 ? (
              <EmptyPanel title="No projects yet" description="Create the first project to bind uploads and outputs." />
            ) : null}
          </div>
        </SectionCard>
      </div>
    </PlatformLayout>
  );
}

function ProjectScreen({ projectId }: { projectId: string }) {
  const router = useRouter();
  const workspaceId = extractWorkspaceId(usePathname());
  const [project, setProject] = useState<ProjectSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  async function refresh() {
    try {
      const row = await getProject(projectId);
      setProject(row);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "The project could not be loaded.");
    }
  }

  useEffect(() => {
    void refresh();
  }, [projectId]);

  async function onUpload(files: FileList | null) {
    const file = files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const result = await uploadDirect(file, projectId);
      await refresh();
      const destination = resolveUploadedFileDestination(
        workspaceId,
        { original_filename: file.name, content_type: file.type || null },
        result.file_id
      );
      router.push(destination.href);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <PlatformLayout title={project?.name || "Project"} subtitle="Project workspace">
      <div className="mx-auto flex w-full max-w-[1320px] flex-col gap-6 px-4 py-6 lg:px-8">
        <section className="rounded-[28px] border border-[#e5e7eb] bg-white p-6 shadow-[0_16px_42px_rgba(15,23,42,0.04)]">
          <label className="flex cursor-pointer flex-col items-center justify-center rounded-[28px] border border-dashed border-[#d7dfde] bg-[#fcfcfb] px-6 py-12 text-center">
            <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#6b7280]">Upload</div>
            <div className="mt-3 text-2xl font-semibold tracking-[-0.04em] text-[#111827]">{uploading ? "Uploading..." : "Add a file to this project."}</div>
            <div className="mt-3 text-sm text-[#6b7280]">The file opens in the correct app and stays attached to this project.</div>
            <input type="file" className="hidden" onChange={(event) => void onUpload(event.target.files)} />
          </label>
          {error ? <div className="mt-3 text-sm text-[#b42318]">{error}</div> : null}
        </section>

        <SectionCard title="Files" description="Uploads, outputs, and generated artifacts">
          <div className="grid gap-4 lg:grid-cols-2">
            {(project?.files || []).map((file) => (
              <div key={file.file_id} className="rounded-[24px] border border-[#d7dfde] bg-white p-4">
                <div className="flex items-center justify-between gap-4">
                  <div className="min-w-0">
                    <div className="truncate text-sm font-semibold text-[#111827]">{file.original_filename}</div>
                    <div className="mt-1 text-xs text-[#6b7280]">{file.kind || "file"} / {file.mode || "default"}</div>
                  </div>
                  <StatusBadge label={file.status} />
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  <Link href={resolveAppHref(workspaceId, appForFile(file), file.file_id)} className="rounded-full bg-[var(--accent)] px-3 py-2 text-xs font-medium text-white hover:opacity-95">
                    Open app
                  </Link>
                  <Link href={resolveFileOpenHref(workspaceId, file.file_id)} className="rounded-full border border-[#d7dfde] px-3 py-2 text-xs text-[#374151] hover:bg-[#f4f7f6]">
                    Viewer
                  </Link>
                </div>
              </div>
            ))}
            {!project?.files?.length ? <EmptyPanel title="No files in project" description="Upload a file or generate a job output to populate this project." /> : null}
          </div>
        </SectionCard>
      </div>
    </PlatformLayout>
  );
}

function FilesScreen() {
  const router = useRouter();
  const workspaceId = extractWorkspaceId(usePathname());
  const workspace = useWorkspaceData();
  const [selectedProjectId, setSelectedProjectId] = useState("all");
  const [shareLinks, setShareLinks] = useState<Record<string, string>>({});
  const [shareErrors, setShareErrors] = useState<Record<string, string>>({});
  const [sharingFileId, setSharingFileId] = useState<string | null>(null);
  const [copiedFileId, setCopiedFileId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  const filteredFiles = selectedProjectId === "all"
    ? workspace.files
    : workspace.files.filter((file) => {
        const project = workspace.projects.find((item) => item.files?.some((projectFile) => projectFile.file_id === file.file_id));
        return project?.id === selectedProjectId;
      });

  async function onUpload(files: FileList | null, projectId?: string) {
    const file = files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const result = await uploadDirect(file, projectId);
      await workspace.refresh();
      setError(null);
      const destination = resolveUploadedFileDestination(
        workspaceId,
        { original_filename: file.name, content_type: file.type || null },
        result.file_id
      );
      router.push(destination.href);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setUploading(false);
    }
  }

  async function onShare(fileId: string) {
    setSharingFileId(fileId);
    setShareErrors((prev) => {
      const next = { ...prev };
      delete next[fileId];
      return next;
    });
    try {
      const result = await createShare(fileId, 7 * 24 * 60 * 60);
      setShareLinks((prev) => ({ ...prev, [fileId]: `${window.location.origin}/s/${result.token}` }));
      setCopiedFileId(null);
    } catch (err) {
      setShareErrors((prev) => ({
        ...prev,
        [fileId]: err instanceof Error ? err.message : "The share link could not be created.",
      }));
    } finally {
      setSharingFileId(null);
    }
  }

  async function onCopyShare(fileId: string) {
    const shareLink = shareLinks[fileId];
    if (!shareLink) return;
    if (typeof navigator === "undefined" || !navigator.clipboard?.writeText) {
      setShareErrors((prev) => ({
        ...prev,
        [fileId]: "Clipboard access is unavailable in this browser.",
      }));
      return;
    }
    try {
      await navigator.clipboard.writeText(shareLink);
      setCopiedFileId(fileId);
      setShareErrors((prev) => {
        const next = { ...prev };
        delete next[fileId];
        return next;
      });
    } catch (err) {
      setShareErrors((prev) => ({
        ...prev,
        [fileId]: err instanceof Error ? err.message : "The share link could not be copied.",
      }));
    }
  }

  return (
    <PlatformLayout title="Files & Share" subtitle="Upload, open, and share">
      <div className="mx-auto flex w-full max-w-[1480px] flex-col gap-5 px-4 py-5 lg:px-6">
        <section className="rounded-[28px] border border-[#e5e7eb] bg-white p-6 shadow-[0_16px_42px_rgba(15,23,42,0.04)]">
          <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_280px]">
            <div>
              <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#6b7280]">Upload</div>
              <div className="mt-3 text-3xl font-semibold tracking-[-0.04em] text-[#111827]">Add a file and open the right workspace.</div>
              <div className="mt-5 flex flex-col gap-3 md:flex-row">
                <select
                  value={selectedProjectId}
                  onChange={(event) => setSelectedProjectId(event.target.value)}
                  className="h-12 min-w-[220px] rounded-2xl border border-[#e5e7eb] bg-white px-4 text-sm text-[#111827] outline-none"
                >
                  <option value="all">All projects</option>
                  {workspace.projects.map((project) => (
                    <option key={project.id} value={project.id}>
                      {project.name}
                    </option>
                  ))}
                </select>
                <label className="flex h-12 cursor-pointer items-center justify-center rounded-2xl bg-[var(--accent)] px-5 text-sm font-medium text-white hover:opacity-95">
                  {uploading ? "Uploading..." : "Upload file"}
                  <input
                    type="file"
                    className="hidden"
                    onChange={(event) => void onUpload(event.target.files, selectedProjectId === "all" ? undefined : selectedProjectId)}
                  />
                </label>
              </div>
              {error ? <div className="mt-3 text-sm text-[#b42318]">{error}</div> : null}
            </div>

            <div className="rounded-[20px] border border-[#e5e7eb] bg-[#fcfcfb] p-4">
              <div className="text-xs uppercase tracking-[0.18em] text-[#6b7280]">Scope</div>
              <div className="mt-2 text-sm text-[#111827]">
                {selectedProjectId === "all"
                  ? "Showing files from every project."
                  : `Showing files for project ${selectedProjectId}.`}
              </div>
              <div className="mt-4 text-xs text-[#6b7280]">{filteredFiles.length} visible file{filteredFiles.length === 1 ? "" : "s"}</div>
            </div>
          </div>
        </section>

        <section className="overflow-hidden rounded-[24px] border border-[#e5e7eb] bg-white shadow-[0_12px_30px_rgba(15,23,42,0.04)]">
          <div className="grid grid-cols-[minmax(0,1.4fr)_150px_170px_auto] gap-3 border-b border-[#e5e7eb] px-5 py-4 text-xs font-semibold uppercase tracking-[0.18em] text-[#6b7280]">
            <div>File</div>
            <div>Status</div>
            <div>Surface</div>
            <div>Actions</div>
          </div>
          {workspace.loading ? <div className="px-5 py-6 text-sm text-[#6b7280]">Loading files...</div> : null}
          {!workspace.loading && filteredFiles.length === 0 ? (
            <div className="px-5 py-6">
              <EmptyPanel title="No files available" description="Upload a file to start the routing and share flow." />
            </div>
          ) : null}
          {!workspace.loading ? (
            <div>
              {filteredFiles.map((file) => {
                const appId = appForFile(file);
                const surfaceCopy = fileRouteCopy(appId);
                return (
                  <div key={file.file_id} className="grid grid-cols-[minmax(0,1.4fr)_150px_170px_auto] gap-3 border-b border-[#f1f5f9] px-5 py-4 last:border-b-0">
                    <div className="min-w-0">
                      <div className="truncate text-sm font-semibold text-[#111827]">{file.original_filename}</div>
                      <div className="mt-1 text-xs text-[#6b7280]">
                        {file.kind} / {file.mode || "default"} / {formatBytes(file.size_bytes)}
                      </div>
                    </div>
                    <div className="flex items-center">
                      <StatusBadge label={file.status} />
                    </div>
                    <div className="flex items-center">
                      <div className="rounded-full border border-[#e5e7eb] px-3 py-1 text-xs text-[#4b5563]">
                        {surfaceCopy.label}
                      </div>
                    </div>
                    <div className="flex flex-col items-start gap-2">
                      <div className="flex flex-wrap items-center gap-2">
                        <Link href={resolveAppHref(workspaceId, appId, file.file_id)} className="rounded-full bg-[var(--accent)] px-3 py-2 text-xs font-medium text-white hover:opacity-95">
                          Open app
                        </Link>
                        <Link href={resolveFileOpenHref(workspaceId, file.file_id)} className="rounded-full border border-[#e5e7eb] px-3 py-2 text-xs text-[#374151] hover:bg-[#f8fafc]">
                          Viewer
                        </Link>
                        <button
                          type="button"
                          onClick={() => void onShare(file.file_id)}
                          disabled={sharingFileId === file.file_id}
                          className="rounded-full border border-[#e5e7eb] px-3 py-2 text-xs text-[#374151] hover:bg-[#f8fafc] disabled:cursor-not-allowed disabled:opacity-60"
                        >
                          {sharingFileId === file.file_id ? "Creating..." : shareLinks[file.file_id] ? "Refresh link" : "Share"}
                        </button>
                        {shareLinks[file.file_id] ? (
                          <>
                            <a
                              href={shareLinks[file.file_id]}
                              target="_blank"
                              rel="noreferrer"
                              className="rounded-full border border-[#cfe0dc] bg-[#f1f8f7] px-3 py-2 text-xs text-[#1f5c57] hover:bg-[#e8f3f1]"
                            >
                              Open link
                            </a>
                            <button
                              type="button"
                              onClick={() => void onCopyShare(file.file_id)}
                              className="rounded-full border border-[#cfe0dc] bg-[#f1f8f7] px-3 py-2 text-xs text-[#1f5c57] hover:bg-[#e8f3f1]"
                            >
                              {copiedFileId === file.file_id ? "Copied" : "Copy link"}
                            </button>
                          </>
                        ) : null}
                      </div>
                      {shareErrors[file.file_id] ? (
                        <div className="text-xs text-[#b42318]">{shareErrors[file.file_id]}</div>
                      ) : null}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : null}
        </section>
      </div>
    </PlatformLayout>
  );
}

function LibraryScreen() {
  const workspace = useWorkspaceData();
  const [feed, setFeed] = useState<LibraryItem[]>([]);
  const [publishFileId, setPublishFileId] = useState("");
  const [title, setTitle] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    try {
      const data = await getLibraryFeed({ page_size: 12 });
      setFeed(data.items);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "The library feed could not be loaded.");
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function onPublish() {
    if (!publishFileId) return;
    try {
      await publishLibraryItem({
        file_id: publishFileId,
        visibility: "public",
        title: title || undefined,
      });
      setPublishFileId("");
      setTitle("");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Publish failed.");
    }
  }

  return (
    <PlatformLayout title="Library" subtitle="Shared assets and publish flow">
      <div className="mx-auto flex w-full max-w-[1320px] flex-col gap-6 px-4 py-6 lg:px-8">
        <SectionCard title="Publish Ready File" description="Publishes a real file into the library feed.">
          <div className="grid gap-3 md:grid-cols-[1fr_1fr_auto]">
            <select
              value={publishFileId}
              onChange={(event) => setPublishFileId(event.target.value)}
              className="h-12 rounded-2xl border border-[#d7dfde] bg-white px-4 text-sm text-[#111827] outline-none"
            >
              <option value="">Select ready file</option>
              {workspace.files
                .filter((file) => file.status === "ready")
                .map((file) => (
                  <option key={file.file_id} value={file.file_id}>
                    {file.original_filename}
                  </option>
                ))}
            </select>
            <input
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Public library title"
              className="h-12 rounded-2xl border border-[#d7dfde] bg-white px-4 text-sm text-[#111827] outline-none placeholder:text-[#111827]/30"
            />
            <button type="button" onClick={() => void onPublish()} className="h-12 rounded-2xl bg-white px-5 text-sm font-medium text-black hover:bg-white/90">
              Publish
            </button>
          </div>
          {error ? <div className="mt-3 text-sm text-[#b42318]">{error}</div> : null}
        </SectionCard>

        <SectionCard title="Feed" description="Public catalog items returned from the backend feed endpoint.">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {feed.map((item) => (
              <div key={item.id} className="rounded-[24px] border border-[#d7dfde] bg-white p-5">
                <div className="text-sm font-semibold text-[#111827]">{item.title}</div>
                <div className="mt-2 text-sm text-[#6b7280]">{item.description || "No description"}</div>
                <div className="mt-4 text-xs text-[#6b7280]">{item.slug}</div>
              </div>
            ))}
            {feed.length === 0 ? <EmptyPanel title="Library is empty" description="Publish a ready file to make the first catalog item visible." /> : null}
          </div>
        </SectionCard>
      </div>
    </PlatformLayout>
  );
}

function SettingsScreen() {
  const { user, isAuthenticated } = useUser();

  return (
    <PlatformLayout title="Plans" subtitle="Suite identity, access tiers, and packaging rules">
      <div className="mx-auto flex w-full max-w-[1320px] flex-col gap-6 px-4 py-6 lg:px-8">
        <SectionCard title="Workspace Identity" description="Guest and authenticated sessions use the same platform shell.">
          <div className="rounded-[24px] border border-[#d7dfde] bg-white p-5 text-sm text-[#1f2937]">
            <div>User: {user.name}</div>
            <div className="mt-2">Mode: {isAuthenticated ? "Authenticated" : "Guest"}</div>
            <div className="mt-2">Role: {user.role}</div>
          </div>
        </SectionCard>

        <SectionCard title="Plans" description="The suite stays on Free / Plus / Pro. Pricing stays secondary to the product workflow.">
          <div className="grid gap-4 md:grid-cols-3">
            {SUITE_PLAN_ROWS.map((plan) => (
              <div key={plan.name} className="rounded-[24px] border border-[#d7dfde] bg-white p-5">
                <div className="text-lg font-semibold text-[#111827]">{plan.name}</div>
                <div className="mt-2 text-sm font-medium uppercase tracking-[0.2em] text-[#6b7280]">{plan.headline}</div>
                <div className="mt-3 text-sm text-[#6b7280]">{plan.description}</div>
              </div>
            ))}
          </div>
        </SectionCard>

        <SectionCard title="Suite Packaging" description="Apps can ship separately without turning STELLCODEX into disconnected products.">
          <div className="grid gap-4 lg:grid-cols-3">
            <div className="rounded-[24px] border border-[#d7dfde] bg-white p-5 text-sm text-[#4b5563]">
              One shared core keeps files, projects, identity, routing, and access rules consistent across every app.
            </div>
            <div className="rounded-[24px] border border-[#d7dfde] bg-white p-5 text-sm text-[#4b5563]">
              Separate mobile packages can expose one focused app surface while the main STELLCODEX suite remains the canonical experience.
            </div>
            <div className="rounded-[24px] border border-[#d7dfde] bg-white p-5 text-sm text-[#4b5563]">
              The interface stays ad-free and workflow-first. Plans describe access scope, not in-product sales clutter.
            </div>
          </div>
        </SectionCard>
      </div>
    </PlatformLayout>
  );
}

function AdminScreen() {
  const [buildId, setBuildId] = useState("loading");
  const [apiHealth, setApiHealth] = useState("loading");
  const [stellHealth, setStellHealth] = useState("loading");

  useEffect(() => {
    fetch("/build_id.txt", { cache: "no-store" })
      .then((res) => (res.ok ? res.text() : "unavailable"))
      .then(setBuildId)
      .catch(() => setBuildId("unavailable"));
    fetch("/api/v1/health", { cache: "no-store" })
      .then((res) => (res.ok ? res.text() : `HTTP ${res.status}`))
      .then(setApiHealth)
      .catch(() => setApiHealth("unavailable"));
    fetch("/stell/health", { cache: "no-store" })
      .then((res) => (res.ok ? res.text() : `HTTP ${res.status}`))
      .then(setStellHealth)
      .catch(() => setStellHealth("unavailable"));
  }, []);

  return (
    <PlatformLayout title="Admin" subtitle="Role-gated release and health overview">
      <div className="mx-auto flex w-full max-w-[1320px] flex-col gap-6 px-4 py-6 lg:px-8">
        <SectionCard title="Release Gate" description="Deploy proof and health endpoints visible from the admin route.">
          <div className="grid gap-4 lg:grid-cols-3">
            <div className="rounded-[24px] border border-[#d7dfde] bg-white p-5">
              <div className="text-sm font-semibold text-[#111827]">build_id.txt</div>
              <pre className="mt-3 overflow-x-auto whitespace-pre-wrap text-xs text-[#4b5563]">{buildId}</pre>
            </div>
            <div className="rounded-[24px] border border-[#d7dfde] bg-white p-5">
              <div className="text-sm font-semibold text-[#111827]">/api/v1/health</div>
              <pre className="mt-3 whitespace-pre-wrap text-xs text-[#4b5563]">{apiHealth}</pre>
            </div>
            <div className="rounded-[24px] border border-[#d7dfde] bg-white p-5">
              <div className="text-sm font-semibold text-[#111827]">/stell/health</div>
              <pre className="mt-3 whitespace-pre-wrap text-xs text-[#4b5563]">{stellHealth}</pre>
            </div>
          </div>
        </SectionCard>
        <SectionCard title="Known Blockers" description="Only variable names are exposed; secrets are never rendered in the UI.">
          <BlockerPanel
            title="Social provider credentials missing"
            description="Social connect and publishing remain intentionally hidden until these environment keys exist on the deployed stack."
            blockerKeys={SOCIAL_OAUTH_BLOCKERS}
          />
        </SectionCard>
      </div>
    </PlatformLayout>
  );
}

function ViewerScreen({ fileId }: { fileId: string }) {
  const workspaceId = extractWorkspaceId(usePathname());
  const [file, setFile] = useState<FileDetail | null>(null);
  const [status, setStatus] = useState<string>("loading");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    async function load() {
      try {
        const data = await getFile(fileId);
        if (!mounted) return;
        setFile(data);
        setStatus(data.status);
        if (data.status !== "ready") {
          const state = await getFileStatus(fileId);
          if (!mounted) return;
          setStatus(state.state || data.status);
        }
        setError(null);
      } catch (err) {
        if (!mounted) return;
        setError(err instanceof Error ? err.message : "The viewer could not be loaded.");
      }
    }
    void load();
    return () => {
      mounted = false;
    };
  }, [fileId]);

  const ready = file?.status === "ready" || status === "succeeded" || status === "ready";
  const appId = file ? appForFile(file) : "viewer3d";
  const viewerCopy = viewerSurfaceContent(appId);
  const viewerTheme = viewerSurfaceTheme(appId);

  return (
    <PlatformLayout title={file?.original_filename || viewerCopy.label} subtitle={viewerCopy.description} mode="focus">
      <div className="grid w-full gap-4 px-3 py-3 lg:grid-cols-[minmax(0,1fr)_320px] lg:px-4">
        {error ? <EmptyPanel title="Viewer unavailable" description={error} /> : null}
        <section className={`overflow-hidden rounded-[28px] border ${viewerTheme.stageShell}`}>
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#e5e7eb] bg-white/88 px-4 py-3">
            <div className="flex items-center gap-2">
              <span className="rounded-full border border-[#e5e7eb] px-3 py-1 text-xs uppercase tracking-[0.18em] text-[#6b7280]">
                {viewerTheme.badge}
              </span>
              {file ? <StatusBadge label={file.status} /> : null}
            </div>
            <div className="text-xs text-[#6b7280]">{file?.original_filename || fileId}</div>
          </div>
          {!error && !ready ? (
            <div className="grid min-h-[640px] place-items-center px-6 py-12">
              <div className="text-center">
                <div className="text-base font-semibold text-[#111827]">Processing file</div>
                <div className="mt-2 text-sm text-[#4b5563]">Current state: {status}</div>
              </div>
            </div>
          ) : null}
          {ready ? (
            <iframe
              src={`/view/${fileId}`}
              className={`h-[calc(100dvh-165px)] min-h-[680px] w-full ${viewerTheme.frameTone}`}
              title="STELLCODEX viewer"
            />
          ) : null}
        </section>

        <div className="space-y-4">
          <SectionCard title="Actions" description="Keep only the actions needed for the current file.">
            <div className="flex flex-col gap-2">
              <Link href={resolveAppHref(workspaceId, appId, fileId)} className="rounded-2xl bg-[var(--accent)] px-4 py-3 text-sm font-medium text-white hover:opacity-95">
                Open in {viewerCopy.label}
              </Link>
              <Link href={buildStandaloneViewerPath(fileId)} className="rounded-2xl border border-[#e5e7eb] px-4 py-3 text-sm text-[#374151] hover:bg-[#f8fafc]">
                Open deep link
              </Link>
            </div>
          </SectionCard>
          <SectionCard title={viewerTheme.sideTitle} description={viewerTheme.sideDescription}>
            <div className="space-y-2">
              {viewerTheme.tips.map((tip) => (
                <div key={tip} className="rounded-[18px] border border-[#e5e7eb] bg-[#fcfcfb] px-4 py-3 text-sm text-[#374151]">
                  {tip}
                </div>
              ))}
            </div>
          </SectionCard>
        </div>
      </div>
    </PlatformLayout>
  );
}

function RecordWorkspace({
  projectId,
  kind,
  title,
  description,
  fields,
  initialPayload,
  publishBuilder,
  publishDescription,
  onArtifactCreated,
}: {
  projectId: string;
  kind: string;
  title: string;
  description: string;
  fields: RecordField[];
  initialPayload: Record<string, unknown>;
  publishBuilder?: (payload: Record<string, unknown>) => PublishDocument | null;
  publishDescription?: string;
  onArtifactCreated?: () => Promise<void>;
}) {
  const [payload, setPayload] = useState<Record<string, unknown>>(initialPayload);
  const [records, setRecords] = useState<PersistedRecord[]>([]);
  const [busy, setBusy] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editingRecordId, setEditingRecordId] = useState<string | null>(null);
  const [publishedUrl, setPublishedUrl] = useState<string | null>(null);
  const [publishedFileId, setPublishedFileId] = useState<string | null>(null);

  async function refresh() {
    try {
      const rows = await loadLatestRecords(projectId, kind);
      setRecords(rows);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Records could not be loaded.");
    }
  }

  useEffect(() => {
    void refresh();
  }, [kind, projectId]);

  useEffect(() => {
    setPayload(initialPayload);
    setEditingRecordId(null);
  }, [kind, projectId]);

  async function onSave() {
    setBusy(true);
    try {
      await saveRecordFile({
        projectId,
        kind,
        title: String(payload.title || title),
        payload,
        recordId: editingRecordId || undefined,
      });
      await refresh();
      setEditingRecordId(null);
      setPayload(initialPayload);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "The record could not be saved.");
    } finally {
      setBusy(false);
    }
  }

  async function onDelete() {
    if (!editingRecordId) return;
    setBusy(true);
    try {
      await saveRecordFile({
        projectId,
        kind,
        title: String(payload.title || title),
        payload,
        recordId: editingRecordId,
        deleted: true,
      });
      await refresh();
      setEditingRecordId(null);
      setPayload(initialPayload);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "The record could not be deleted.");
    } finally {
      setBusy(false);
    }
  }

  function onEdit(record: PersistedRecord) {
    setEditingRecordId(record.record_id);
    setPayload(record.payload);
    setError(null);
  }

  function onReset() {
    setEditingRecordId(null);
    setPayload(initialPayload);
    setError(null);
  }

  async function waitForFileReady(fileId: string) {
    for (let attempt = 0; attempt < 40; attempt += 1) {
      const state = await getFileStatus(fileId);
      if (state.state === "succeeded" || state.state === "ready") return;
      if (state.state === "failed") {
        throw new Error("Published page processing failed.");
      }
      await new Promise((resolve) => window.setTimeout(resolve, 750));
    }
    throw new Error("Published page did not become ready in time.");
  }

  async function onPublish() {
    if (!publishBuilder) return;
    setPublishing(true);
    setError(null);
    try {
      const document = publishBuilder(payload);
      if (!document) throw new Error("Publish content could not be generated.");
      const artifact = new File([document.html], document.filename, { type: "text/html" });
      const uploaded = await uploadDirect(artifact, projectId);
      await waitForFileReady(uploaded.file_id);
      const share = await createShare(uploaded.file_id, document.expiresInSeconds);
      await onArtifactCreated?.();
      setPublishedFileId(uploaded.file_id);
      setPublishedUrl(`${window.location.origin}/s/${share.token}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Publish failed.");
    } finally {
      setPublishing(false);
    }
  }

  return (
    <SectionCard title={title} description={description}>
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="space-y-3">
          {fields.map((field) => (
            <label key={field.key} className="block">
              <div className="mb-2 text-xs uppercase tracking-[0.2em] text-[#6b7280]">{field.label}</div>
              {field.type === "textarea" ? (
                <textarea
                  value={String(payload[field.key] || "")}
                  onChange={(event) => setPayload((prev) => ({ ...prev, [field.key]: event.target.value }))}
                  rows={5}
                  placeholder={field.placeholder}
                  className="w-full rounded-2xl border border-[#d7dfde] bg-white px-4 py-3 text-sm text-[#111827] outline-none placeholder:text-[#111827]/30"
                />
              ) : field.type === "select" ? (
                <select
                  value={String(payload[field.key] || "")}
                  onChange={(event) => setPayload((prev) => ({ ...prev, [field.key]: event.target.value }))}
                  className="h-12 w-full rounded-2xl border border-[#d7dfde] bg-white px-4 text-sm text-[#111827] outline-none"
                >
                  {field.options?.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  type={field.type === "number" ? "number" : field.type === "date" ? "date" : "text"}
                  value={String(payload[field.key] || "")}
                  onChange={(event) =>
                    setPayload((prev) => ({
                      ...prev,
                      [field.key]: field.type === "number" ? Number(event.target.value || 0) : event.target.value,
                    }))
                  }
                  placeholder={field.placeholder}
                  className="h-12 w-full rounded-2xl border border-[#d7dfde] bg-white px-4 text-sm text-[#111827] outline-none placeholder:text-[#111827]/30"
                />
              )}
            </label>
          ))}
          <div className="flex flex-wrap gap-3">
            <button type="button" onClick={() => void onSave()} disabled={busy} className="rounded-2xl bg-[#0f766e] px-5 py-3 text-sm font-medium text-white hover:bg-[#0c5f59] disabled:cursor-not-allowed disabled:opacity-60">
              {busy ? "Saving..." : editingRecordId ? "Update record" : "Save record"}
            </button>
            {publishBuilder ? (
              <button type="button" onClick={() => void onPublish()} disabled={busy || publishing} className="rounded-2xl border border-[#b7d9d5] px-5 py-3 text-sm font-medium text-[#0f766e] hover:bg-[#eef8f6] disabled:cursor-not-allowed disabled:opacity-60">
                {publishing ? "Publishing..." : "Publish live page"}
              </button>
            ) : null}
            <button type="button" onClick={onReset} disabled={busy} className="rounded-2xl border border-[#d7dfde] px-5 py-3 text-sm font-medium text-[#1f2937] hover:bg-[#f4f7f6] disabled:cursor-not-allowed disabled:opacity-60">
              New record
            </button>
            {editingRecordId ? (
              <button type="button" onClick={() => void onDelete()} disabled={busy} className="rounded-2xl border border-[#f1c9c9] px-5 py-3 text-sm font-medium text-[#b42318] hover:bg-[#fff5f5] disabled:cursor-not-allowed disabled:opacity-60">
                Delete record
              </button>
            ) : null}
          </div>
          {publishDescription ? <div className="text-xs text-[#6b7280]">{publishDescription}</div> : null}
          {error ? <div className="text-sm text-[#b42318]">{error}</div> : null}
          {publishedUrl ? (
            <div className="rounded-[20px] border border-[#b7d9d5] bg-[#eef8f6] p-4 text-sm text-[#0f766e]">
              <div className="font-semibold">Published link is live</div>
              <a href={publishedUrl} target="_blank" rel="noreferrer" className="mt-2 block break-all text-[#0f766e] underline underline-offset-4">
                {publishedUrl}
              </a>
              {publishedFileId ? <div className="mt-2 text-xs text-[#0f766e]/80">artifact file_id: {publishedFileId}</div> : null}
            </div>
          ) : null}
        </div>
        <div className="space-y-3">
          {records.map((record) => (
            <div key={record.record_id} className="rounded-[20px] border border-[#d7dfde] bg-white p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-[#111827]">{record.title}</div>
                  <div className="mt-1 text-xs text-[#6b7280]">{formatDate(record.saved_at)}</div>
                </div>
                <button type="button" onClick={() => onEdit(record)} className="rounded-full border border-[#d7dfde] px-3 py-1 text-xs text-[#374151] hover:bg-[#f4f7f6]">
                  Edit
                </button>
              </div>
              <pre className="mt-3 overflow-x-auto whitespace-pre-wrap text-xs text-[#4b5563]">{JSON.stringify(record.payload, null, 2)}</pre>
            </div>
          ))}
          {records.length === 0 ? <EmptyPanel title="No saved records" description="Saving creates a real backend file artifact tied to the selected project." /> : null}
        </div>
      </div>
    </SectionCard>
  );
}

function AppRunnerScreen({ appId, fileId = "" }: { appId: string; fileId?: string }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const workspace = useWorkspaceData();
  const { user } = useUser();
  const resolvedAppId = getPlatformApp(appId)?.id || resolveMarketplaceCoreAppId(appId) || appId;
  const app = getPlatformApp(resolvedAppId);
  const isMarketplaceAlias = appId !== resolvedAppId;
  const [selectedProjectId, setSelectedProjectId] = useState("default");
  const searchFileId = searchParams.get("file_id") || "";
  const [selectedFileId, setSelectedFileId] = useState(fileId || searchFileId);
  const [selectedFile, setSelectedFile] = useState<FileDetail | null>(null);
  const [marketplaceItem, setMarketplaceItem] = useState<AppsCatalogItem | null>(null);
  const [job, setJob] = useState<JobStatus | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [shareUrl, setShareUrl] = useState<string | null>(null);
  const [moldCategory, setMoldCategory] = useState<keyof typeof MOLD_CATALOG>("plates");
  const [moldFamily, setMoldFamily] = useState("base-a");
  const [moldWidth, setMoldWidth] = useState(200);
  const [moldHeight, setMoldHeight] = useState(240);
  const [moldThickness, setMoldThickness] = useState(24);
  const [moldMaterial, setMoldMaterial] = useState("1.2311");
  const completedJobRef = useRef<string | null>(null);
  const workspaceId = extractWorkspaceId(pathname);

  useEffect(() => {
    if (!app) return;
    if (app.adminOnly && user.role !== "admin") {
      router.replace(resolveWorkspaceHref(workspaceId, "/"));
    }
  }, [app, router, user.role, workspaceId]);

  useEffect(() => {
    setSelectedFileId(fileId || searchFileId);
  }, [fileId, searchFileId]);

  useEffect(() => {
    if (workspace.projects.length > 0 && !workspace.projects.some((project) => project.id === selectedProjectId)) {
      setSelectedProjectId(workspace.projects[0].id);
    }
  }, [selectedProjectId, workspace.projects]);

  useEffect(() => {
    if (!selectedFileId) {
      setSelectedFile(null);
      return;
    }
    let mounted = true;
    getFile(selectedFileId)
      .then((file) => {
        if (!mounted) return;
        setSelectedFile(file);
      })
      .catch((err) => {
        if (!mounted) return;
        setError(err instanceof Error ? err.message : "The file could not be loaded.");
      });
    return () => {
      mounted = false;
    };
  }, [selectedFileId]);

  useEffect(() => {
    if (!jobId) return;
    let mounted = true;
    async function poll() {
      try {
        const next = await getJob(jobId);
        if (!mounted) return;
        setJob(next);
        if ((next.status === "finished" || next.status === "failed") && completedJobRef.current !== next.job_id) {
          completedJobRef.current = next.job_id;
          await workspace.refresh();
        }
      } catch (err) {
        if (!mounted) return;
        setError(err instanceof Error ? err.message : "The job status could not be loaded.");
      }
    }
    void poll();
    const timer = window.setInterval(() => {
      void poll();
    }, 1500);
    return () => {
      mounted = false;
      window.clearInterval(timer);
    };
  }, [jobId, workspace]);

  useEffect(() => {
    if (!isMarketplaceAlias) {
      setMarketplaceItem(null);
      return;
    }
    let active = true;
    listAppsCatalog(true)
      .then((rows) => {
        if (!active) return;
        setMarketplaceItem(rows.find((item) => item.slug === appId) || null);
      })
      .catch(() => {
        if (!active) return;
        setMarketplaceItem(null);
      });
    return () => {
      active = false;
    };
  }, [appId, isMarketplaceAlias]);

  if (!app) {
    return <MarketplaceModuleScreen slug={appId} />;
  }

  const projectOptions = workspace.projects.length > 0 ? workspace.projects : [{ id: "default", name: "Default Project", file_count: 0 }];
  const selectedProject = projectOptions.find((project) => project.id === selectedProjectId) || projectOptions[0];
  const surface = app.surface;
  const relevantFiles = workspace.files.filter((file) => {
    if (app.id === "viewer2d") return appForFile(file) === "viewer2d";
    if (app.id === "docviewer") return appForFile(file) === "docviewer";
    if (["viewer3d", "convert", "mesh2d3d"].includes(app.id)) return appForFile(file) === "viewer3d";
    return true;
  });
  const familyConfig = getMoldFamilyConfig(moldCategory, moldFamily);
  const moldConfigId = `${moldCategory}-${moldFamily}-${moldWidth}x${moldHeight}-${moldThickness}-${moldMaterial}`.toLowerCase();
  const outputFileId = extractOutputFileId(job);
  const viewerCopy = viewerSurfaceContent(surface);
  const readyViewerFileId = outputFileId || selectedFileId;

  async function onRun() {
    setError(null);
    setShareUrl(null);
    try {
      if (app.id === "convert" && selectedFileId) {
        const next = await enqueueConvert(selectedFileId);
        setJobId(next.job_id);
        setJob(next);
        return;
      }
      if (app.id === "mesh2d3d" && selectedFileId) {
        const next = await enqueueMesh2d3d(selectedFileId);
        setJobId(next.job_id);
        setJob(next);
        return;
      }
      if (app.id === "moldcodes") {
        if (
          moldWidth < familyConfig.minWidth ||
          moldWidth > familyConfig.maxWidth ||
          moldHeight < familyConfig.minHeight ||
          moldHeight > familyConfig.maxHeight ||
          moldThickness < familyConfig.minThickness ||
          moldThickness > familyConfig.maxThickness
        ) {
          setError("Configurator values are outside the allowed family limits.");
          return;
        }
        const next = await enqueueMoldcodesExport({
          project_id: selectedProject.id,
          category: moldCategory,
          family: moldFamily,
          params: {
            width_mm: moldWidth,
            height_mm: moldHeight,
            thickness_mm: moldThickness,
            material: moldMaterial,
            configId: moldConfigId,
          },
        });
        await saveRecordFile({
          projectId: selectedProject.id,
          kind: "moldcodes-bom",
          title: `MoldCodes ${moldConfigId}`,
          payload: {
            project_id: selectedProject.id,
            category: moldCategory,
            family: moldFamily,
            width_mm: moldWidth,
            height_mm: moldHeight,
            thickness_mm: moldThickness,
            material: moldMaterial,
            configId: moldConfigId,
          },
        });
        setJobId(next.job_id);
        setJob(next);
        return;
      }
      if (["viewer3d", "viewer2d", "docviewer"].includes(app.id) && selectedFileId) {
        return;
      }
      if (app.id === "library") {
        router.push(resolveWorkspaceHref(workspaceId, "/library"));
        return;
      }
      if (app.id === "drive") {
        router.push(resolveWorkspaceHref(workspaceId, "/files"));
        return;
      }
      if (app.id === "projects") {
        router.push(resolveWorkspaceHref(workspaceId, "/projects"));
        return;
      }
      if (app.id === "admin") {
        router.push(resolveWorkspaceHref(workspaceId, "/admin"));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Run failed.");
    }
  }

  async function onCreateShare() {
    if (!selectedFileId) return;
    try {
      const result = await createShare(selectedFileId, 7 * 24 * 60 * 60);
      setShareUrl(`${window.location.origin}/s/${result.token}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "The share link could not be created.");
    }
  }

  async function onDownloadOutput(fileId: string) {
    try {
      const blobUrl = await fetchAuthedBlobUrl(`/api/v1/files/${encodeURIComponent(fileId)}/download`);
      window.open(blobUrl, "_blank", "noopener,noreferrer");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Download failed.");
    }
  }

  function renderProjectSelector(description: string) {
    return (
      <SectionCard title="Project Context" description={description}>
        <label className="block">
          <div className="mb-2 text-xs uppercase tracking-[0.2em] text-[#6b7280]">Project</div>
          <select value={selectedProject.id} onChange={(event) => setSelectedProjectId(event.target.value)} className="h-12 w-full rounded-2xl border border-[#d7dfde] bg-white px-4 text-sm text-[#111827] outline-none">
            {projectOptions.map((project) => (
              <option key={project.id} value={project.id}>
                {project.name}
              </option>
            ))}
          </select>
        </label>
        <div className="mt-4 rounded-[20px] border border-[#d7dfde] bg-white p-4">
          <div className="text-sm font-semibold text-[#111827]">{selectedProject.name}</div>
          <div className="mt-1 text-xs text-[#6b7280]">{selectedProject.id}</div>
          <div className="mt-3 text-xs text-[#4b5563]">{selectedProject.file_count || 0} linked files in the current project scope.</div>
        </div>
      </SectionCard>
    );
  }

  function renderFileSelector(title: string, description: string) {
    return (
      <SectionCard title={title} description={description}>
        <label className="block">
          <div className="mb-2 text-xs uppercase tracking-[0.2em] text-[#6b7280]">Source file</div>
          <select value={selectedFileId} onChange={(event) => setSelectedFileId(event.target.value)} className="h-12 w-full rounded-2xl border border-[#d7dfde] bg-white px-4 text-sm text-[#111827] outline-none">
            <option value="">Select file</option>
            {relevantFiles.map((file) => (
              <option key={file.file_id} value={file.file_id}>
                {file.original_filename}
              </option>
            ))}
          </select>
        </label>
        {selectedFile ? (
          <div className="mt-4 rounded-[20px] border border-[#d7dfde] bg-white p-4">
            <div className="truncate text-sm font-semibold text-[#111827]">{selectedFile.original_filename}</div>
            <div className="mt-2 flex flex-wrap gap-2">
              <StatusBadge label={selectedFile.status || "unknown"} />
              <span className="rounded-full border border-[#d7dfde] px-2.5 py-1 text-xs text-[#4b5563]">{titleCase(selectedFile.kind || "file")}</span>
              <span className="rounded-full border border-[#d7dfde] px-2.5 py-1 text-xs text-[#4b5563]">{titleCase(selectedFile.mode || "default")}</span>
            </div>
            <div className="mt-3 text-xs text-[#6b7280]">file_id: {selectedFile.file_id}</div>
          </div>
        ) : (
          <div className="mt-4 text-sm text-[#6b7280]">Only files that match this application surface are listed here.</div>
        )}
      </SectionCard>
    );
  }

  function renderOverview() {
    return (
      <SectionCard title={app.name} description={app.summary}>
        <div className="grid gap-4 lg:grid-cols-2">
          <div className="rounded-[24px] border border-[#d7dfde] bg-white p-5">
            <div className="text-xs uppercase tracking-[0.2em] text-[#6b7280]">Surface</div>
            <div className="mt-3 text-sm text-[#374151]">{titleCase(app.surface)}</div>
          </div>
          <div className="rounded-[24px] border border-[#d7dfde] bg-white p-5">
            <div className="text-xs uppercase tracking-[0.2em] text-[#6b7280]">Project</div>
            <div className="mt-3 text-sm text-[#374151]">{selectedProject.name}</div>
            <div className="mt-1 text-xs text-[#6b7280]">{selectedProject.id}</div>
          </div>
        </div>
      </SectionCard>
    );
  }

  function renderInputs() {
    if (app.id === "moldcodes") {
      return (
        <SectionCard title="Inputs" description="Category, family and validated dimensions feed the export job.">
          <div className="grid gap-4 lg:grid-cols-2">
            <label className="block">
              <div className="mb-2 text-xs uppercase tracking-[0.2em] text-[#6b7280]">Project</div>
              <select value={selectedProject.id} onChange={(event) => setSelectedProjectId(event.target.value)} className="h-12 w-full rounded-2xl border border-[#d7dfde] bg-white px-4 text-sm text-[#111827] outline-none">
                {projectOptions.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="block">
              <div className="mb-2 text-xs uppercase tracking-[0.2em] text-[#6b7280]">Category</div>
              <select value={moldCategory} onChange={(event) => {
                const nextCategory = event.target.value as keyof typeof MOLD_CATALOG;
                const nextFamily = Object.keys(MOLD_CATALOG[nextCategory].families)[0];
                setMoldCategory(nextCategory);
                setMoldFamily(nextFamily);
              }} className="h-12 w-full rounded-2xl border border-[#d7dfde] bg-white px-4 text-sm text-[#111827] outline-none">
                {Object.entries(MOLD_CATALOG).map(([key, value]) => (
                  <option key={key} value={key}>
                    {value.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="block">
              <div className="mb-2 text-xs uppercase tracking-[0.2em] text-[#6b7280]">Family</div>
              <select value={moldFamily} onChange={(event) => setMoldFamily(event.target.value)} className="h-12 w-full rounded-2xl border border-[#d7dfde] bg-white px-4 text-sm text-[#111827] outline-none">
                {Object.entries(MOLD_CATALOG[moldCategory].families).map(([key, value]) => (
                  <option key={key} value={key}>
                    {value.label}
                  </option>
                ))}
              </select>
            </label>
            <div className="rounded-[24px] border border-[#d7dfde] bg-white p-4 text-sm text-[#4b5563]">
              configId: <span className="text-[#111827]">{moldConfigId}</span>
            </div>
            <label className="block">
              <div className="mb-2 text-xs uppercase tracking-[0.2em] text-[#6b7280]">Width (mm)</div>
              <input type="number" value={moldWidth} onChange={(event) => setMoldWidth(Number(event.target.value || 0))} className="h-12 w-full rounded-2xl border border-[#d7dfde] bg-white px-4 text-sm text-[#111827] outline-none" />
            </label>
            <label className="block">
              <div className="mb-2 text-xs uppercase tracking-[0.2em] text-[#6b7280]">Height (mm)</div>
              <input type="number" value={moldHeight} onChange={(event) => setMoldHeight(Number(event.target.value || 0))} className="h-12 w-full rounded-2xl border border-[#d7dfde] bg-white px-4 text-sm text-[#111827] outline-none" />
            </label>
            <label className="block">
              <div className="mb-2 text-xs uppercase tracking-[0.2em] text-[#6b7280]">Thickness (mm)</div>
              <input type="number" value={moldThickness} onChange={(event) => setMoldThickness(Number(event.target.value || 0))} className="h-12 w-full rounded-2xl border border-[#d7dfde] bg-white px-4 text-sm text-[#111827] outline-none" />
            </label>
            <label className="block">
              <div className="mb-2 text-xs uppercase tracking-[0.2em] text-[#6b7280]">Material</div>
              <input value={moldMaterial} onChange={(event) => setMoldMaterial(event.target.value)} className="h-12 w-full rounded-2xl border border-[#d7dfde] bg-white px-4 text-sm text-[#111827] outline-none" />
            </label>
          </div>
          <div className="mt-4 text-xs text-[#6b7280]">
            Allowed range: {familyConfig.minWidth}-{familyConfig.maxWidth} mm width, {familyConfig.minHeight}-{familyConfig.maxHeight} mm height, {familyConfig.minThickness}-{familyConfig.maxThickness} mm thickness.
          </div>
        </SectionCard>
      );
    }

    if (["socialmanager", "feedpublisher"].includes(app.id)) {
      return (
        <>
          <BlockerPanel
            title="OAuth provider blocker"
            description="Posting and live account connection stay hidden until provider credentials exist in the deployment environment."
            blockerKeys={SOCIAL_OAUTH_BLOCKERS}
          />
          <EmptyPanel
            title="Inputs are saved through record workspaces"
            description="Use the records section below to store draft accounts and scheduler records without exposing non-working OAuth actions."
          />
        </>
      );
    }

    if (["accounting", "webbuilder", "cms"].includes(app.id)) {
      return (
        <EmptyPanel
          title="Inputs are saved through record workspaces"
          description="Use the records section below to edit and persist records into project-backed JSON artifacts."
        />
      );
    }

    return (
      <div className="grid gap-4 lg:grid-cols-2">
        {renderProjectSelector("Keep every run attached to a real project scope.")}
        {renderFileSelector("Source File", "Pick the exact source file that this application should process.")}
      </div>
    );
  }

  function renderRun() {
    if (["socialmanager", "feedpublisher"].includes(app.id)) {
      return (
        <SectionCard title="Run" description="Blocked actions stay hidden until the provider credentials are available.">
          <BlockerPanel
            title="Publish actions hidden"
            description="This MVP only stores account and feed drafts. Real OAuth connect and posting remain disabled because the required Meta application secrets are not configured."
            blockerKeys={SOCIAL_OAUTH_BLOCKERS}
          />
        </SectionCard>
      );
    }

    if (["accounting", "webbuilder", "cms"].includes(app.id)) {
      return (
        <SectionCard title="Run" description="These MVP apps persist records directly; no worker execution is required.">
          <div className="text-sm text-[#4b5563]">
            Use the records section below to create or update persisted records.
            {["webbuilder", "cms"].includes(app.id) ? " Web apps can also publish a real /s token link from the current draft." : ""}
          </div>
        </SectionCard>
      );
    }
    return (
      <SectionCard title="Run" description="Only working actions are exposed.">
        <div className="flex flex-wrap gap-3">
          <button type="button" onClick={() => void onRun()} className="rounded-2xl bg-[#0f766e] px-5 py-3 text-sm font-medium text-white hover:bg-[#0c5f59]">
            {["viewer3d", "viewer2d", "docviewer"].includes(app.id) ? "Open viewer" : "Run"}
          </button>
          {selectedFileId ? (
            <button type="button" onClick={() => void onCreateShare()} className="rounded-2xl border border-[#d7dfde] px-5 py-3 text-sm text-[#1f2937] hover:bg-[#f4f7f6]">
              Create share
            </button>
          ) : null}
        </div>
        {shareUrl ? <div className="mt-4 rounded-[24px] border border-[#b7d9d5] bg-[#eef8f6] px-4 py-3 text-sm text-[#0f766e]">{shareUrl}</div> : null}
        {error ? <div className="mt-4 text-sm text-[#b42318]">{error}</div> : null}
      </SectionCard>
    );
  }

  function renderProgress() {
    if (!job) {
      return <EmptyPanel title="No active job" description="Run the application to populate worker queue progress." />;
    }
    return (
      <SectionCard title="Progress" description="Worker status returned from /api/v1/jobs/:job_id">
        <div className="grid gap-4 lg:grid-cols-2">
          <div className="rounded-[24px] border border-[#d7dfde] bg-white p-5">
            <div className="text-xs uppercase tracking-[0.2em] text-[#6b7280]">Job</div>
            <div className="mt-3 text-sm text-[#111827]">{job.job_id}</div>
            <div className="mt-2"><StatusBadge label={job.status} /></div>
            <div className="mt-3 text-xs text-[#6b7280]">Queued: {formatDate(job.enqueued_at)}</div>
            <div className="mt-1 text-xs text-[#6b7280]">Started: {formatDate(job.started_at)}</div>
            <div className="mt-1 text-xs text-[#6b7280]">Ended: {formatDate(job.ended_at)}</div>
          </div>
          <div className="rounded-[24px] border border-[#d7dfde] bg-white p-5">
            <div className="text-xs uppercase tracking-[0.2em] text-[#6b7280]">Meta</div>
            <pre className="mt-3 overflow-x-auto whitespace-pre-wrap text-xs text-[#4b5563]">{JSON.stringify(job.meta || {}, null, 2)}</pre>
          </div>
        </div>
        {job.error ? <div className="mt-4 rounded-[24px] border border-red-500/20 bg-red-500/8 px-4 py-3 text-sm text-red-100">{job.error}</div> : null}
      </SectionCard>
    );
  }

  function renderOutput() {
    if (app.id === "accounting") {
      return (
        <RecordWorkspace
          projectId={selectedProject.id}
          kind="accounting-entry"
          title="Accounting Records"
          description="Invoices, income and expenses persist as backend JSON artifacts."
          initialPayload={{ title: "Invoice draft", entryType: "invoice", counterparty: "", amount: 0, currency: "USD", dueDate: "", notes: "" }}
          fields={[
            { key: "title", label: "Title", type: "text", placeholder: "Invoice March 2026" },
            { key: "entryType", label: "Entry Type", type: "select", options: ["invoice", "income", "expense"] },
            { key: "counterparty", label: "Counterparty", type: "text", placeholder: "Customer or supplier" },
            { key: "amount", label: "Amount", type: "number" },
            { key: "currency", label: "Currency", type: "select", options: ["USD", "EUR", "TRY"] },
            { key: "dueDate", label: "Due Date", type: "date" },
            { key: "notes", label: "Notes", type: "textarea", placeholder: "Internal accounting notes" },
          ]}
        />
      );
    }

    if (app.id === "socialmanager") {
      return (
        <div className="space-y-4">
          <BlockerPanel
            title="Social OAuth blocked"
            description="Secure provider connect cannot be completed on this deployment because the Meta OAuth credentials are missing. Posting and live connection actions remain hidden."
            blockerKeys={SOCIAL_OAUTH_BLOCKERS}
          />
          <RecordWorkspace
            projectId={selectedProject.id}
            kind="social-account"
            title="Social Accounts"
            description="Draft account ownership and onboarding notes persist per project without claiming a live connection."
            initialPayload={{ title: "Instagram account", network: "instagram", accountLabel: "", connectionState: "draft", owner: "", notes: "" }}
            fields={[
              { key: "title", label: "Title", type: "text", placeholder: "Instagram account" },
              { key: "network", label: "Network", type: "select", options: ["instagram", "linkedin", "x", "facebook"] },
              { key: "accountLabel", label: "Account Label", type: "text", placeholder: "@stellcodex" },
              { key: "connectionState", label: "Connection State", type: "select", options: ["draft", "blocked"] },
              { key: "owner", label: "Owner", type: "text", placeholder: "Growth team" },
              { key: "notes", label: "Notes", type: "textarea", placeholder: "Blocked until META_APP_ID and META_APP_SECRET exist." },
            ]}
          />
        </div>
      );
    }

    if (app.id === "feedpublisher") {
      return (
        <div className="space-y-4">
          <BlockerPanel
            title="Publishing blocked"
            description="Feed drafts are stored, but publish and scheduler execution remain hidden until the live Meta OAuth credentials are configured."
            blockerKeys={SOCIAL_OAUTH_BLOCKERS}
          />
          <RecordWorkspace
            projectId={selectedProject.id}
            kind="feed-draft"
            title="Feed Publisher"
            description="Scheduler drafts and captions persist per project without exposing a non-working publish action."
            initialPayload={{ title: "Launch post", channel: "instagram", publishAt: "", caption: "", assetFileId: selectedFileId }}
            fields={[
              { key: "title", label: "Title", type: "text", placeholder: "Launch post" },
              { key: "channel", label: "Channel", type: "select", options: ["instagram", "linkedin", "x", "facebook"] },
              { key: "publishAt", label: "Publish At", type: "date" },
              { key: "assetFileId", label: "Asset File Id", type: "text", placeholder: "Optional file_id" },
              { key: "caption", label: "Caption", type: "textarea", placeholder: "Write the post draft" },
            ]}
          />
        </div>
      );
    }

    if (app.id === "webbuilder") {
      return (
        <RecordWorkspace
          projectId={selectedProject.id}
          kind="web-page"
          title="Web Builder"
          description="Create, save and publish page drafts with real persistence."
          initialPayload={{ title: "Landing page", slug: "landing-page", headline: "", body: "", ctaLabel: "Contact sales" }}
          publishBuilder={(payload) => buildPublishedPage("webbuilder", payload)}
          publishDescription="Publish uploads a real HTML artifact to the selected project and exposes it through a live /s token."
          onArtifactCreated={workspace.refresh}
          fields={[
            { key: "title", label: "Title", type: "text", placeholder: "Landing page" },
            { key: "slug", label: "Slug", type: "text", placeholder: "landing-page" },
            { key: "headline", label: "Headline", type: "text", placeholder: "Production intelligence for manufacturing" },
            { key: "ctaLabel", label: "CTA Label", type: "text", placeholder: "Contact sales" },
            { key: "body", label: "Body", type: "textarea", placeholder: "Page body content" },
          ]}
        />
      );
    }

    if (app.id === "cms") {
      return (
        <RecordWorkspace
          projectId={selectedProject.id}
          kind="cms-entry"
          title="CMS Entries"
          description="Slug, title and body content persist as editable drafts and can be published through a live share link."
          initialPayload={{ title: "Knowledge article", slug: "knowledge-article", body: "", status: "draft" }}
          publishBuilder={(payload) => buildPublishedPage("cms", payload)}
          publishDescription="Publish uploads a real HTML article artifact to the selected project and exposes it through a live /s token."
          onArtifactCreated={workspace.refresh}
          fields={[
            { key: "title", label: "Title", type: "text", placeholder: "Knowledge article" },
            { key: "slug", label: "Slug", type: "text", placeholder: "knowledge-article" },
            { key: "status", label: "Status", type: "select", options: ["draft", "review", "approved"] },
            { key: "body", label: "Body", type: "textarea", placeholder: "CMS content body" },
          ]}
        />
      );
    }

    if (app.id === "drive") {
      return (
        <SectionCard title="Drive Output" description="Inline drive view with the latest workspace files.">
          <div className="grid gap-3 md:grid-cols-2">
            {workspace.files.slice(0, 8).map((file) => (
              <div key={file.file_id} className="rounded-[20px] border border-[#d7dfde] bg-white p-4">
                <div className="truncate text-sm font-semibold text-[#111827]">{file.original_filename}</div>
                <div className="mt-2 text-xs text-[#6b7280]">{file.kind} / {file.status}</div>
              </div>
            ))}
          </div>
        </SectionCard>
      );
    }

    if (app.id === "library") {
      return (
        <SectionCard title="Library Output" description="Open the full library route for publish and feed management.">
          <Link href={resolveWorkspaceHref(workspaceId, "/library")} className="rounded-2xl border border-[#d7dfde] px-5 py-3 text-sm text-[#1f2937] hover:bg-[#f4f7f6]">
            Open library route
          </Link>
        </SectionCard>
      );
    }

    if (app.id === "projects") {
      return (
        <SectionCard title="Projects Output" description="Open the full projects route for project CRUD.">
          <Link href={resolveWorkspaceHref(workspaceId, "/projects")} className="rounded-2xl border border-[#d7dfde] px-5 py-3 text-sm text-[#1f2937] hover:bg-[#f4f7f6]">
            Open projects route
          </Link>
        </SectionCard>
      );
    }

    if (app.id === "status" || app.id === "admin") {
      return (
        <SectionCard title="System Output" description="Use the admin route for release proof and health status.">
          <Link href={resolveWorkspaceHref(workspaceId, "/admin")} className="rounded-2xl border border-[#d7dfde] px-5 py-3 text-sm text-[#1f2937] hover:bg-[#f4f7f6]">
            Open admin route
          </Link>
        </SectionCard>
      );
    }

    if ((["viewer3d", "viewer2d", "docviewer"].includes(app.id) && selectedFileId) || outputFileId) {
      const embeddedFileId = outputFileId || selectedFileId;
      return (
        <SectionCard title="Output" description="Embedded viewer plus download and deep-link actions.">
          <div className="overflow-hidden rounded-[28px] border border-[#d7dfde] bg-[#fbfcfc]">
            <iframe src={`/view/${embeddedFileId}`} className="h-[760px] w-full bg-[#111]" title="Embedded STELLCODEX output" />
          </div>
          <div className="mt-4 flex flex-wrap gap-3">
            <Link href={buildStandaloneViewerPath(embeddedFileId)} className="rounded-2xl border border-[#d7dfde] px-5 py-3 text-sm text-[#1f2937] hover:bg-[#f4f7f6]">
              Open deep link
            </Link>
            <button type="button" onClick={() => void onDownloadOutput(embeddedFileId)} className="rounded-2xl border border-[#d7dfde] px-5 py-3 text-sm text-[#1f2937] hover:bg-[#f4f7f6]">
              Download output
            </button>
          </div>
        </SectionCard>
      );
    }

    return <EmptyPanel title="No output yet" description="Run the app or select a source file to populate output." />;
  }

  function renderViewerSurface() {
    const viewerTheme = viewerSurfaceTheme(surface);
    return (
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_340px]">
        <section className={`overflow-hidden rounded-[28px] border ${viewerTheme.stageShell}`}>
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#e5e7eb] bg-white/88 px-4 py-3">
            <div className="flex items-center gap-2">
              <span className="rounded-full border border-[#e5e7eb] px-3 py-1 text-xs uppercase tracking-[0.18em] text-[#6b7280]">{viewerTheme.badge}</span>
              {selectedFile ? <StatusBadge label={selectedFile.status || "unknown"} /> : null}
            </div>
            <div className="text-xs text-[#6b7280]">{selectedProject.name}</div>
          </div>
          {readyViewerFileId ? (
            <iframe src={`/view/${readyViewerFileId}`} className={`h-[calc(100dvh-180px)] min-h-[680px] w-full ${viewerTheme.frameTone}`} title={`${app.name} workspace stage`} />
          ) : (
            <div className="grid h-[calc(100dvh-180px)] min-h-[680px] place-items-center p-8">
              <EmptyPanel title={viewerCopy.emptyTitle} description={viewerCopy.emptyDescription} />
            </div>
          )}
          <div className="flex flex-wrap gap-3 border-t border-[#e5e7eb] bg-white px-4 py-4">
            {readyViewerFileId ? (
              <Link href={buildStandaloneViewerPath(readyViewerFileId)} className="rounded-2xl bg-[var(--accent)] px-5 py-3 text-sm font-medium text-white hover:opacity-95">
                Open deep link
              </Link>
            ) : null}
            {selectedFileId ? (
              <button type="button" onClick={() => void onCreateShare()} className="rounded-2xl border border-[#e5e7eb] px-5 py-3 text-sm text-[#1f2937] hover:bg-[#f8fafc]">
                Create share
              </button>
            ) : null}
            {readyViewerFileId ? (
              <button type="button" onClick={() => void onDownloadOutput(readyViewerFileId)} className="rounded-2xl border border-[#e5e7eb] px-5 py-3 text-sm text-[#1f2937] hover:bg-[#f8fafc]">
                Download file
              </button>
            ) : null}
          </div>
          {shareUrl ? <div className="border-t border-[#e5e7eb] bg-[#f5fbfa] px-4 py-3 text-sm text-[#1f5c57]">{shareUrl}</div> : null}
          {error ? <div className="border-t border-[#e5e7eb] bg-[#fff7f7] px-4 py-3 text-sm text-[#b42318]">{error}</div> : null}
        </section>

        <div className="space-y-4">
          {renderProjectSelector(viewerCopy.stageDescription)}
          {renderFileSelector("Viewer source", "Only files for this viewer type are listed here.")}
          <SectionCard title={viewerTheme.sideTitle} description={viewerTheme.sideDescription}>
            <div className="space-y-2">
              {viewerTheme.tips.map((tip) => (
                <div key={tip} className="rounded-[18px] border border-[#e5e7eb] bg-[#fcfcfb] px-4 py-3 text-sm text-[#374151]">
                  {tip}
                </div>
              ))}
            </div>
          </SectionCard>
        </div>
      </div>
    );
  }

  function renderJobSurface() {
    return (
      <div className="space-y-6">
        {renderOverview()}
        {renderInputs()}
        {renderRun()}
        {jobId || error ? renderProgress() : null}
        {outputFileId || shareUrl ? renderOutput() : <EmptyPanel title="No output yet" description="Run the job to generate a worker result and output artifact." />}
      </div>
    );
  }

  function renderConfiguratorSurface() {
    return (
      <div className="space-y-6">
        {renderOverview()}
        {renderInputs()}
        {renderRun()}
        {jobId || error ? renderProgress() : null}
        {renderOutput()}
      </div>
    );
  }

  function renderRecordSurface() {
    return (
      <div className="space-y-6">
        {renderOverview()}
        {renderProjectSelector("Records stay bound to one project so the saved artifacts remain easy to find later.")}
        {renderOutput()}
      </div>
    );
  }

  function renderRouteSurface() {
    return (
      <div className="space-y-6">
        {renderOverview()}
        {renderOutput()}
      </div>
    );
  }

  function renderCatalogSurface() {
    return (
      <div className="space-y-6">
        {renderOverview()}
        <SectionCard title="Applications Catalog" description="Open the full app inventory.">
          <div className="flex flex-wrap gap-3">
            <Link href={resolveWorkspaceHref(workspaceId, "/apps")} className="rounded-2xl bg-[#0f766e] px-5 py-3 text-sm font-medium text-white hover:bg-[#0c5f59]">
              Open applications catalog
            </Link>
          </div>
        </SectionCard>
      </div>
    );
  }

  function renderSurface() {
    if (surface === "catalog") return renderCatalogSurface();
    if (surface === "viewer3d" || surface === "viewer2d" || surface === "docviewer") return renderViewerSurface();
    if (surface === "job") return renderJobSurface();
    if (surface === "configurator") return renderConfiguratorSurface();
    if (surface === "records") return renderRecordSurface();
    return renderRouteSurface();
  }

  function renderMarketplaceAliasBanner() {
    if (!isMarketplaceAlias || !marketplaceItem) return null;
    const integration = getMarketplaceIntegration(marketplaceItem);
    return (
      <SectionCard title={marketplaceItem.name} description="This marketplace module resolves into an existing workspace surface.">
        <div className="flex flex-wrap gap-3">
          <StatusBadge label={marketplaceItem.enabled ? "enabled" : "disabled"} />
          <span className="rounded-full border border-[#d7dfde] px-3 py-1 text-xs text-[#4b5563]">{normalizeMarketplaceCategory(marketplaceItem.category)}</span>
          <span className="rounded-full border border-[#d7dfde] px-3 py-1 text-xs text-[#4b5563]">{marketplaceItem.tier}</span>
        </div>
        <div className="mt-4 text-sm text-[#4b5563]">{integration.note}</div>
      </SectionCard>
    );
  }

  return (
    <PlatformLayout title={marketplaceItem?.name || app.name} subtitle={isMarketplaceAlias ? `${app.name} workspace delivery` : app.summary}>
      <div className="mx-auto flex w-full max-w-[1480px] flex-col gap-6 px-4 py-6 lg:px-8">
        {renderMarketplaceAliasBanner()}
        {renderSurface()}
      </div>
    </PlatformLayout>
  );
}

export function PlatformClient({ view, appId = "", projectId = "", fileId = "" }: PlatformClientProps) {
  if (view === "home") return <HomeScreen />;
  if (view === "apps") return <AppsCatalogScreen />;
  if (view === "projects") return <ProjectsScreen />;
  if (view === "project") return <ProjectScreen projectId={projectId} />;
  if (view === "files") return <FilesScreen />;
  if (view === "library") return <LibraryScreen />;
  if (view === "settings") return <SettingsScreen />;
  if (view === "admin") return <AdminScreen />;
  if (view === "viewer") return <ViewerScreen fileId={fileId} />;
  return <AppRunnerScreen appId={appId} fileId={fileId} />;
}
