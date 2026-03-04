"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useUser } from "@/context/UserContext";
import { getPlatformApp, getVisiblePlatformApps, platformApps, PlatformAppId } from "@/data/platformCatalog";
import { loadLatestRecords, saveRecordFile, type PersistedRecord } from "@/lib/fileRecords";
import {
  appendSessionMessage,
  loadActiveSessionId,
  loadSessions,
  newSession,
  saveActiveSessionId,
  saveSessions,
  upsertSession,
  type WorkspaceSession,
} from "@/lib/sessionStore";
import {
  ApiHttpError,
  createProject,
  createShare,
  enqueueConvert,
  enqueueMesh2d3d,
  enqueueMoldcodesExport,
  fetchAuthedBlobUrl,
  getFile,
  getFileStatus,
  getJob,
  getLibraryFeed,
  getProject,
  listFiles,
  listProjects,
  publishLibraryItem,
  type FileDetail,
  type FileItem,
  type JobStatus,
  type LibraryItem,
  type ProjectSummary,
  uploadDirect,
} from "@/services/api";
import { PlatformLayout } from "./PlatformLayout";

type PlatformView = "home" | "app" | "projects" | "project" | "files" | "library" | "settings" | "admin" | "viewer";

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

type RunnerTab = "Overview" | "Inputs" | "Run" | "Progress" | "Output";

const RUNNER_TABS: RunnerTab[] = ["Overview", "Inputs", "Run", "Progress", "Output"];

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
  return date.toLocaleString("tr-TR", {
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

function appForFile(file: FileItem | FileDetail) {
  const name = file.original_filename.toLowerCase();
  if (name.endsWith(".dxf")) return "viewer2d";
  if (file.content_type === "application/pdf" || file.content_type.startsWith("image/")) return "docviewer";
  return "viewer3d";
}

function formatBytes(size?: number | null) {
  if (!size) return "0 B";
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
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
      setError(err instanceof Error ? err.message : "Workspace verisi yuklenemedi.");
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
    <section className="rounded-[28px] border border-white/10 bg-white/[0.03] p-5 shadow-[0_0_0_1px_rgba(255,255,255,0.02)]">
      <div className="mb-4">
        <div className="text-lg font-semibold text-white">{title}</div>
        {description ? <div className="mt-1 text-sm text-white/45">{description}</div> : null}
      </div>
      {children}
    </section>
  );
}

function StatusBadge({ label }: { label: string }) {
  const tone =
    label === "ready" || label === "finished" || label === "ok"
      ? "border-emerald-500/25 bg-emerald-500/10 text-emerald-200"
      : label === "failed"
      ? "border-red-500/25 bg-red-500/10 text-red-200"
      : "border-amber-500/25 bg-amber-500/10 text-amber-200";
  return <span className={`rounded-full border px-2.5 py-1 text-xs ${tone}`}>{titleCase(label)}</span>;
}

function EmptyPanel({ title, description }: { title: string; description: string }) {
  return (
    <div className="rounded-[24px] border border-dashed border-white/12 bg-black/10 p-6 text-sm text-white/55">
      <div className="font-medium text-white/80">{title}</div>
      <div className="mt-1">{description}</div>
    </div>
  );
}

function HomeScreen() {
  const router = useRouter();
  const { user } = useUser();
  const [sessions, setSessions] = useState<WorkspaceSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");

  useEffect(() => {
    const stored = loadSessions();
    if (stored.length > 0) {
      setSessions(stored);
      setActiveSessionId(loadActiveSessionId() || stored[0].id);
      return;
    }
    const created = newSession();
    saveSessions([created]);
    saveActiveSessionId(created.id);
    setSessions([created]);
    setActiveSessionId(created.id);
  }, []);

  const activeSession = sessions.find((item) => item.id === activeSessionId) || sessions[0] || null;
  const visibleApps = getVisiblePlatformApps(user.role);

  function onSelectSession(sessionId: string) {
    setActiveSessionId(sessionId);
    saveActiveSessionId(sessionId);
  }

  function onNewSession() {
    const created = newSession();
    const next = [created, ...sessions];
    saveSessions(next);
    saveActiveSessionId(created.id);
    setSessions(next);
    setActiveSessionId(created.id);
  }

  function onSendMessage() {
    if (!activeSession || !draft.trim()) return;
    const userMessage = appendSessionMessage(activeSession, "user", draft.trim());
    const reply = appendSessionMessage(
      userMessage,
      "assistant",
      "Bu istegi bir STELLCODEX uygulamasina yonlendirebilirsiniz. Files ile yukleme, Projects ile proje acma veya Explore Applications ile uygun runner secimi hazir."
    );
    const next = upsertSession(reply);
    setSessions(next);
    setActiveSessionId(reply.id);
    setDraft("");
  }

  return (
    <PlatformLayout
      title={activeSession?.title || "Workspace"}
      subtitle="Single entry platform with sessions and embedded applications"
      sessionState={{ sessions, activeSessionId, onSelectSession, onNewSession }}
    >
      <div className="mx-auto flex h-full w-full max-w-[1600px] flex-col px-4 py-6 lg:px-8">
        <div className="flex-1 rounded-[32px] border border-white/10 bg-[linear-gradient(180deg,rgba(255,255,255,0.04),rgba(255,255,255,0.01))]">
          <div className="mx-auto flex h-full max-w-[960px] flex-col gap-6 px-4 py-8 lg:px-8">
            <div className="pt-8 text-center">
              <div className="text-3xl font-semibold tracking-tight text-white">What can STELLCODEX help build today?</div>
              <div className="mt-2 text-sm text-white/45">
                Upload files, open projects, run mesh jobs and manage platform applications from one workspace.
              </div>
            </div>

            <div className="flex flex-1 flex-col gap-4">
              {activeSession?.messages.map((message) => (
                <div
                  key={message.id}
                  className={`max-w-[760px] rounded-[24px] px-5 py-4 text-sm leading-6 ${
                    message.role === "assistant"
                      ? "bg-white/[0.04] text-white/85"
                      : "ml-auto bg-[#303030] text-white"
                  }`}
                >
                  {message.text}
                </div>
              ))}
            </div>

            <SectionCard title="Explore Applications" description="Only live, wired modules are exposed.">
              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                {visibleApps.map((app) => (
                  <button
                    key={app.id}
                    type="button"
                    onClick={() => router.push(app.route)}
                    className="rounded-[24px] border border-white/10 bg-black/10 p-4 text-left transition hover:border-white/20 hover:bg-white/[0.05]"
                  >
                    <div className="flex items-center justify-between">
                      <div className="text-sm font-semibold text-white">{app.name}</div>
                      <div className="rounded-full border border-white/10 px-2 py-1 text-[11px] text-white/45">{app.category}</div>
                    </div>
                    <div className="mt-2 text-sm text-white/55">{app.summary}</div>
                  </button>
                ))}
              </div>
            </SectionCard>

            <div className="sticky bottom-0 rounded-[28px] border border-white/10 bg-[#2a2a2a] p-3 shadow-[0_30px_80px_rgba(0,0,0,0.35)]">
              <textarea
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                rows={3}
                placeholder="Describe the task, then switch into the right application..."
                className="w-full resize-none bg-transparent px-3 py-2 text-sm text-white outline-none placeholder:text-white/30"
              />
              <div className="flex items-center justify-between border-t border-white/8 pt-3">
                <div className="flex flex-wrap gap-2 text-xs text-white/35">
                  <span className="rounded-full border border-white/10 px-3 py-1">Files upload</span>
                  <span className="rounded-full border border-white/10 px-3 py-1">Mesh jobs</span>
                  <span className="rounded-full border border-white/10 px-3 py-1">Mold export</span>
                </div>
                <button
                  type="button"
                  onClick={onSendMessage}
                  className="rounded-full bg-white px-4 py-2 text-sm font-medium text-black hover:bg-white/90"
                >
                  Send
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </PlatformLayout>
  );
}

function ProjectsScreen() {
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
      setError(err instanceof Error ? err.message : "Projeler yuklenemedi.");
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
      setError(err instanceof Error ? err.message : "Proje olusturulamadi.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <PlatformLayout title="Projects" subtitle="Create, open and attach files to real projects">
      <div className="mx-auto flex w-full max-w-[1320px] flex-col gap-6 px-4 py-6 lg:px-8">
        <SectionCard title="Create Project" description="Projects are persisted in the backend contract.">
          <div className="flex flex-col gap-3 md:flex-row">
            <input
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="Injection tooling package"
              className="h-12 flex-1 rounded-2xl border border-white/10 bg-black/10 px-4 text-sm text-white outline-none placeholder:text-white/30"
            />
            <button
              type="button"
              onClick={onCreate}
              disabled={busy}
              className="h-12 rounded-2xl bg-white px-5 text-sm font-medium text-black hover:bg-white/90 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {busy ? "Creating..." : "Create project"}
            </button>
          </div>
          {error ? <div className="mt-3 text-sm text-red-200">{error}</div> : null}
        </SectionCard>

        <SectionCard title="Project Index" description="All project-backed uploads and exports remain retrievable later.">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {projects.map((project) => (
              <Link
                key={project.id}
                href={`/project/${project.id}`}
                className="rounded-[24px] border border-white/10 bg-black/10 p-5 transition hover:border-white/20 hover:bg-white/[0.04]"
              >
                <div className="flex items-center justify-between">
                  <div className="text-base font-semibold text-white">{project.name}</div>
                  <div className="text-xs text-white/40">{project.file_count} files</div>
                </div>
                <div className="mt-3 text-sm text-white/45">Updated {formatDate(project.updated_at)}</div>
              </Link>
            ))}
            {projects.length === 0 ? (
              <EmptyPanel title="No projects yet" description="Create the first project to bind uploads, jobs and generated outputs." />
            ) : null}
          </div>
        </SectionCard>
      </div>
    </PlatformLayout>
  );
}

function ProjectScreen({ projectId }: { projectId: string }) {
  const [project, setProject] = useState<ProjectSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  async function refresh() {
    try {
      const row = await getProject(projectId);
      setProject(row);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Proje yuklenemedi.");
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
      await uploadDirect(file, projectId);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Yukleme basarisiz.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <PlatformLayout title={project?.name || "Project"} subtitle={projectId}>
      <div className="mx-auto flex w-full max-w-[1320px] flex-col gap-6 px-4 py-6 lg:px-8">
        <SectionCard title="Project Upload" description="Files uploaded here stay attached to this project id.">
          <label className="flex cursor-pointer flex-col items-center justify-center rounded-[28px] border border-dashed border-white/12 bg-black/10 px-6 py-12 text-center">
            <div className="text-sm font-medium text-white">{uploading ? "Uploading..." : "Upload file to project"}</div>
            <div className="mt-2 text-sm text-white/45">STEP, STL, DXF, PDF, images or JSON records</div>
            <input type="file" className="hidden" onChange={(event) => void onUpload(event.target.files)} />
          </label>
          {error ? <div className="mt-3 text-sm text-red-200">{error}</div> : null}
        </SectionCard>

        <SectionCard title="Project Files" description="Outputs, uploads and generated artifacts are listed together.">
          <div className="grid gap-4 lg:grid-cols-2">
            {(project?.files || []).map((file) => (
              <div key={file.file_id} className="rounded-[24px] border border-white/10 bg-black/10 p-4">
                <div className="flex items-center justify-between gap-4">
                  <div className="min-w-0">
                    <div className="truncate text-sm font-semibold text-white">{file.original_filename}</div>
                    <div className="mt-1 text-xs text-white/40">{file.kind || "file"} / {file.mode || "default"}</div>
                  </div>
                  <StatusBadge label={file.status} />
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  <Link href={`/viewer/${file.file_id}`} className="rounded-full border border-white/10 px-3 py-1 text-xs text-white/70 hover:bg-white/8">
                    Open viewer
                  </Link>
                  <Link href={`/app/${file.kind === "2d" ? "viewer2d" : "viewer3d"}?file_id=${encodeURIComponent(file.file_id)}`} className="rounded-full border border-white/10 px-3 py-1 text-xs text-white/70 hover:bg-white/8">
                    Open runner
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
  const workspace = useWorkspaceData();
  const [selectedProjectId, setSelectedProjectId] = useState("all");
  const [shareLinks, setShareLinks] = useState<Record<string, string>>({});
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
      await uploadDirect(file, projectId);
      await workspace.refresh();
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Yukleme basarisiz.");
    } finally {
      setUploading(false);
    }
  }

  async function onShare(fileId: string) {
    try {
      const result = await createShare(fileId, 7 * 24 * 60 * 60);
      setShareLinks((prev) => ({ ...prev, [fileId]: `${window.location.origin}/s/${result.token}` }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Share olusturulamadi.");
    }
  }

  return (
    <PlatformLayout title="Files" subtitle="Upload, view, share and track processing state">
      <div className="mx-auto flex w-full max-w-[1320px] flex-col gap-6 px-4 py-6 lg:px-8">
        <SectionCard title="Upload" description="Uploads return file_id and immediately attach to the selected project.">
          <div className="flex flex-col gap-3 md:flex-row">
            <select
              value={selectedProjectId}
              onChange={(event) => setSelectedProjectId(event.target.value)}
              className="h-12 rounded-2xl border border-white/10 bg-black/10 px-4 text-sm text-white outline-none"
            >
              <option value="all">All projects</option>
              {workspace.projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
            <label className="flex h-12 cursor-pointer items-center justify-center rounded-2xl bg-white px-5 text-sm font-medium text-black hover:bg-white/90">
              {uploading ? "Uploading..." : "Select file"}
              <input
                type="file"
                className="hidden"
                onChange={(event) => void onUpload(event.target.files, selectedProjectId === "all" ? undefined : selectedProjectId)}
              />
            </label>
          </div>
          {error ? <div className="mt-3 text-sm text-red-200">{error}</div> : null}
        </SectionCard>

        <SectionCard title="File Ledger" description="Only live actions are shown: open viewer, open runner and create share.">
          {workspace.loading ? <div className="text-sm text-white/45">Loading files...</div> : null}
          {!workspace.loading ? (
            <div className="grid gap-4 lg:grid-cols-2">
              {filteredFiles.map((file) => (
                <div key={file.file_id} className="rounded-[24px] border border-white/10 bg-black/10 p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0">
                      <div className="truncate text-sm font-semibold text-white">{file.original_filename}</div>
                      <div className="mt-1 text-xs text-white/40">
                        {file.kind} / {file.mode || "default"} / {formatBytes(file.size_bytes)}
                      </div>
                    </div>
                    <StatusBadge label={file.status} />
                  </div>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <Link href={`/viewer/${file.file_id}`} className="rounded-full border border-white/10 px-3 py-1 text-xs text-white/70 hover:bg-white/8">
                      View
                    </Link>
                    <Link
                      href={`/app/${appForFile(file)}?file_id=${encodeURIComponent(file.file_id)}`}
                      className="rounded-full border border-white/10 px-3 py-1 text-xs text-white/70 hover:bg-white/8"
                    >
                      Open in app
                    </Link>
                    <button
                      type="button"
                      onClick={() => void onShare(file.file_id)}
                      className="rounded-full border border-white/10 px-3 py-1 text-xs text-white/70 hover:bg-white/8"
                    >
                      Create share
                    </button>
                  </div>
                  {shareLinks[file.file_id] ? (
                    <div className="mt-3 rounded-2xl border border-emerald-500/20 bg-emerald-500/8 px-3 py-2 text-xs text-emerald-100">
                      {shareLinks[file.file_id]}
                    </div>
                  ) : null}
                </div>
              ))}
              {!filteredFiles.length ? <EmptyPanel title="No files available" description="Upload a file to start the processing and viewer flow." /> : null}
            </div>
          ) : null}
        </SectionCard>
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
      setError(err instanceof Error ? err.message : "Library feed yuklenemedi.");
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
      setError(err instanceof Error ? err.message : "Publish basarisiz.");
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
              className="h-12 rounded-2xl border border-white/10 bg-black/10 px-4 text-sm text-white outline-none"
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
              className="h-12 rounded-2xl border border-white/10 bg-black/10 px-4 text-sm text-white outline-none placeholder:text-white/30"
            />
            <button type="button" onClick={() => void onPublish()} className="h-12 rounded-2xl bg-white px-5 text-sm font-medium text-black hover:bg-white/90">
              Publish
            </button>
          </div>
          {error ? <div className="mt-3 text-sm text-red-200">{error}</div> : null}
        </SectionCard>

        <SectionCard title="Feed" description="Public catalog items returned from the backend feed endpoint.">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {feed.map((item) => (
              <div key={item.id} className="rounded-[24px] border border-white/10 bg-black/10 p-5">
                <div className="text-sm font-semibold text-white">{item.title}</div>
                <div className="mt-2 text-sm text-white/50">{item.description || "No description"}</div>
                <div className="mt-4 text-xs text-white/35">{item.slug}</div>
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
  const plans = [
    { name: "Free", price: "$0", description: "Core workspace, uploads and viewer access." },
    { name: "Plus", price: "$29", description: "Expanded usage and application access." },
    { name: "Pro", price: "$99", description: "Team workflows, advanced jobs and catalogs." },
    { name: "Enterprise", price: "Custom", description: "Governance, audit routing and managed deployment." },
  ];

  return (
    <PlatformLayout title="Settings" subtitle="Plan tiers and workspace identity">
      <div className="mx-auto flex w-full max-w-[1320px] flex-col gap-6 px-4 py-6 lg:px-8">
        <SectionCard title="Workspace Identity" description="Guest and authenticated sessions use the same platform shell.">
          <div className="rounded-[24px] border border-white/10 bg-black/10 p-5 text-sm text-white/75">
            <div>User: {user.name}</div>
            <div className="mt-2">Mode: {isAuthenticated ? "Authenticated" : "Guest"}</div>
            <div className="mt-2">Role: {user.role}</div>
          </div>
        </SectionCard>

        <SectionCard title="Plans" description="Business model is locked to Free / Plus / Pro / Enterprise.">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {plans.map((plan) => (
              <div key={plan.name} className="rounded-[24px] border border-white/10 bg-black/10 p-5">
                <div className="text-lg font-semibold text-white">{plan.name}</div>
                <div className="mt-2 text-3xl font-semibold text-white">{plan.price}</div>
                <div className="mt-3 text-sm text-white/50">{plan.description}</div>
              </div>
            ))}
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
            <div className="rounded-[24px] border border-white/10 bg-black/10 p-5">
              <div className="text-sm font-semibold text-white">build_id.txt</div>
              <pre className="mt-3 overflow-x-auto whitespace-pre-wrap text-xs text-white/60">{buildId}</pre>
            </div>
            <div className="rounded-[24px] border border-white/10 bg-black/10 p-5">
              <div className="text-sm font-semibold text-white">/api/v1/health</div>
              <pre className="mt-3 whitespace-pre-wrap text-xs text-white/60">{apiHealth}</pre>
            </div>
            <div className="rounded-[24px] border border-white/10 bg-black/10 p-5">
              <div className="text-sm font-semibold text-white">/stell/health</div>
              <pre className="mt-3 whitespace-pre-wrap text-xs text-white/60">{stellHealth}</pre>
            </div>
          </div>
        </SectionCard>
      </div>
    </PlatformLayout>
  );
}

function ViewerScreen({ fileId }: { fileId: string }) {
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
        setError(err instanceof Error ? err.message : "Viewer yuklenemedi.");
      }
    }
    void load();
    return () => {
      mounted = false;
    };
  }, [fileId]);

  const ready = file?.status === "ready" || status === "succeeded" || status === "ready";
  const appId = file ? appForFile(file) : "viewer3d";

  return (
    <PlatformLayout title={file?.original_filename || "Viewer"} subtitle={`Deep link for ${fileId}`}>
      <div className="mx-auto flex w-full max-w-[1500px] flex-col gap-6 px-4 py-6 lg:px-8">
        {error ? <EmptyPanel title="Viewer unavailable" description={error} /> : null}
        {!error && !ready ? (
          <SectionCard title="Processing" description="Viewer opens as soon as the backend marks the file ready.">
            <div className="text-sm text-white/60">Current state: {status}</div>
          </SectionCard>
        ) : null}
        {ready ? (
          <SectionCard title="Embedded Viewer" description="Deep-linked into the workspace viewer context.">
            <div className="overflow-hidden rounded-[28px] border border-white/10 bg-black/20">
              <iframe src={`/view/${fileId}`} className="h-[760px] w-full bg-[#111]" title="STELLCODEX viewer" />
            </div>
            <div className="mt-4">
              <Link href={`/app/${appId}?file_id=${encodeURIComponent(fileId)}`} className="rounded-full border border-white/10 px-4 py-2 text-sm text-white/70 hover:bg-white/8">
                Open same file in application runner
              </Link>
            </div>
          </SectionCard>
        ) : null}
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
}: {
  projectId: string;
  kind: string;
  title: string;
  description: string;
  fields: RecordField[];
  initialPayload: Record<string, unknown>;
}) {
  const [payload, setPayload] = useState<Record<string, unknown>>(initialPayload);
  const [records, setRecords] = useState<PersistedRecord[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editingRecordId, setEditingRecordId] = useState<string | null>(null);

  async function refresh() {
    try {
      const rows = await loadLatestRecords(projectId, kind);
      setRecords(rows);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Kayitlar yuklenemedi.");
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
      setError(err instanceof Error ? err.message : "Kayit saklanamadi.");
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
      setError(err instanceof Error ? err.message : "Kayit silinemedi.");
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

  return (
    <SectionCard title={title} description={description}>
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="space-y-3">
          {fields.map((field) => (
            <label key={field.key} className="block">
              <div className="mb-2 text-xs uppercase tracking-[0.2em] text-white/35">{field.label}</div>
              {field.type === "textarea" ? (
                <textarea
                  value={String(payload[field.key] || "")}
                  onChange={(event) => setPayload((prev) => ({ ...prev, [field.key]: event.target.value }))}
                  rows={5}
                  placeholder={field.placeholder}
                  className="w-full rounded-2xl border border-white/10 bg-black/10 px-4 py-3 text-sm text-white outline-none placeholder:text-white/30"
                />
              ) : field.type === "select" ? (
                <select
                  value={String(payload[field.key] || "")}
                  onChange={(event) => setPayload((prev) => ({ ...prev, [field.key]: event.target.value }))}
                  className="h-12 w-full rounded-2xl border border-white/10 bg-black/10 px-4 text-sm text-white outline-none"
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
                  className="h-12 w-full rounded-2xl border border-white/10 bg-black/10 px-4 text-sm text-white outline-none placeholder:text-white/30"
                />
              )}
            </label>
          ))}
          <div className="flex flex-wrap gap-3">
            <button type="button" onClick={() => void onSave()} disabled={busy} className="rounded-2xl bg-white px-5 py-3 text-sm font-medium text-black hover:bg-white/90 disabled:cursor-not-allowed disabled:opacity-60">
              {busy ? "Saving..." : editingRecordId ? "Update record" : "Save record"}
            </button>
            <button type="button" onClick={onReset} disabled={busy} className="rounded-2xl border border-white/10 px-5 py-3 text-sm font-medium text-white/80 hover:bg-white/8 disabled:cursor-not-allowed disabled:opacity-60">
              New record
            </button>
            {editingRecordId ? (
              <button type="button" onClick={() => void onDelete()} disabled={busy} className="rounded-2xl border border-red-500/20 px-5 py-3 text-sm font-medium text-red-200 hover:bg-red-500/10 disabled:cursor-not-allowed disabled:opacity-60">
                Delete record
              </button>
            ) : null}
          </div>
          {error ? <div className="text-sm text-red-200">{error}</div> : null}
        </div>
        <div className="space-y-3">
          {records.map((record) => (
            <div key={record.record_id} className="rounded-[20px] border border-white/10 bg-black/10 p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-white">{record.title}</div>
                  <div className="mt-1 text-xs text-white/35">{formatDate(record.saved_at)}</div>
                </div>
                <button type="button" onClick={() => onEdit(record)} className="rounded-full border border-white/10 px-3 py-1 text-xs text-white/70 hover:bg-white/8">
                  Edit
                </button>
              </div>
              <pre className="mt-3 overflow-x-auto whitespace-pre-wrap text-xs text-white/55">{JSON.stringify(record.payload, null, 2)}</pre>
            </div>
          ))}
          {records.length === 0 ? <EmptyPanel title="No saved records" description="Saving creates a real backend file artifact tied to the selected project." /> : null}
        </div>
      </div>
    </SectionCard>
  );
}

function AppRunnerScreen({ appId }: { appId: string }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const workspace = useWorkspaceData();
  const { user } = useUser();
  const app = getPlatformApp(appId);
  const [activeTab, setActiveTab] = useState<RunnerTab>("Overview");
  const [selectedProjectId, setSelectedProjectId] = useState("default");
  const [selectedFileId, setSelectedFileId] = useState(searchParams.get("file_id") || "");
  const [selectedFile, setSelectedFile] = useState<FileDetail | null>(null);
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

  useEffect(() => {
    if (!app) return;
    if (app.adminOnly && user.role !== "admin") {
      router.replace("/");
    }
  }, [app, router, user.role]);

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
        setError(err instanceof Error ? err.message : "Dosya yuklenemedi.");
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
        setError(err instanceof Error ? err.message : "Job durumu alinamadi.");
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

  if (!app) {
    return (
      <PlatformLayout title="Application not found" subtitle={appId}>
        <div className="mx-auto w-full max-w-[900px] px-4 py-8 lg:px-8">
          <EmptyPanel title="Unknown application" description="Only allowed catalog applications are routable." />
        </div>
      </PlatformLayout>
    );
  }

  const projectOptions = workspace.projects.length > 0 ? workspace.projects : [{ id: "default", name: "Default Project", file_count: 0 }];
  const selectedProject = projectOptions.find((project) => project.id === selectedProjectId) || projectOptions[0];
  const relevantFiles = workspace.files.filter((file) => {
    if (app.id === "viewer2d") return appForFile(file) === "viewer2d";
    if (app.id === "docviewer") return appForFile(file) === "docviewer";
    if (["viewer3d", "convert", "mesh2d3d"].includes(app.id)) return appForFile(file) === "viewer3d";
    return true;
  });
  const familyConfig = getMoldFamilyConfig(moldCategory, moldFamily);
  const moldConfigId = `${moldCategory}-${moldFamily}-${moldWidth}x${moldHeight}-${moldThickness}-${moldMaterial}`.toLowerCase();
  const outputFileId = extractOutputFileId(job);

  async function onRun() {
    setError(null);
    setShareUrl(null);
    setActiveTab("Progress");
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
        setActiveTab("Output");
        return;
      }
      if (app.id === "library") {
        router.push("/library");
        return;
      }
      if (app.id === "drive") {
        router.push("/files");
        return;
      }
      if (app.id === "projects") {
        router.push("/projects");
        return;
      }
      if (app.id === "admin") {
        router.push("/admin");
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
      setError(err instanceof Error ? err.message : "Share olusturulamadi.");
    }
  }

  async function onDownloadOutput(fileId: string) {
    try {
      const blobUrl = await fetchAuthedBlobUrl(`/api/v1/files/${encodeURIComponent(fileId)}/download`);
      window.open(blobUrl, "_blank", "noopener,noreferrer");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Download basarisiz.");
    }
  }

  function renderOverview() {
    return (
      <SectionCard title={app.name} description={app.description}>
        <div className="grid gap-4 lg:grid-cols-2">
          <div className="rounded-[24px] border border-white/10 bg-black/10 p-5">
            <div className="text-xs uppercase tracking-[0.2em] text-white/35">Application Summary</div>
            <div className="mt-3 text-sm text-white/65">{app.summary}</div>
          </div>
          <div className="rounded-[24px] border border-white/10 bg-black/10 p-5">
            <div className="text-xs uppercase tracking-[0.2em] text-white/35">Project Context</div>
            <div className="mt-3 text-sm text-white/65">{selectedProject.name}</div>
            <div className="mt-1 text-xs text-white/35">{selectedProject.id}</div>
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
              <div className="mb-2 text-xs uppercase tracking-[0.2em] text-white/35">Project</div>
              <select value={selectedProject.id} onChange={(event) => setSelectedProjectId(event.target.value)} className="h-12 w-full rounded-2xl border border-white/10 bg-black/10 px-4 text-sm text-white outline-none">
                {projectOptions.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="block">
              <div className="mb-2 text-xs uppercase tracking-[0.2em] text-white/35">Category</div>
              <select value={moldCategory} onChange={(event) => {
                const nextCategory = event.target.value as keyof typeof MOLD_CATALOG;
                const nextFamily = Object.keys(MOLD_CATALOG[nextCategory].families)[0];
                setMoldCategory(nextCategory);
                setMoldFamily(nextFamily);
              }} className="h-12 w-full rounded-2xl border border-white/10 bg-black/10 px-4 text-sm text-white outline-none">
                {Object.entries(MOLD_CATALOG).map(([key, value]) => (
                  <option key={key} value={key}>
                    {value.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="block">
              <div className="mb-2 text-xs uppercase tracking-[0.2em] text-white/35">Family</div>
              <select value={moldFamily} onChange={(event) => setMoldFamily(event.target.value)} className="h-12 w-full rounded-2xl border border-white/10 bg-black/10 px-4 text-sm text-white outline-none">
                {Object.entries(MOLD_CATALOG[moldCategory].families).map(([key, value]) => (
                  <option key={key} value={key}>
                    {value.label}
                  </option>
                ))}
              </select>
            </label>
            <div className="rounded-[24px] border border-white/10 bg-black/10 p-4 text-sm text-white/60">
              configId: <span className="text-white">{moldConfigId}</span>
            </div>
            <label className="block">
              <div className="mb-2 text-xs uppercase tracking-[0.2em] text-white/35">Width (mm)</div>
              <input type="number" value={moldWidth} onChange={(event) => setMoldWidth(Number(event.target.value || 0))} className="h-12 w-full rounded-2xl border border-white/10 bg-black/10 px-4 text-sm text-white outline-none" />
            </label>
            <label className="block">
              <div className="mb-2 text-xs uppercase tracking-[0.2em] text-white/35">Height (mm)</div>
              <input type="number" value={moldHeight} onChange={(event) => setMoldHeight(Number(event.target.value || 0))} className="h-12 w-full rounded-2xl border border-white/10 bg-black/10 px-4 text-sm text-white outline-none" />
            </label>
            <label className="block">
              <div className="mb-2 text-xs uppercase tracking-[0.2em] text-white/35">Thickness (mm)</div>
              <input type="number" value={moldThickness} onChange={(event) => setMoldThickness(Number(event.target.value || 0))} className="h-12 w-full rounded-2xl border border-white/10 bg-black/10 px-4 text-sm text-white outline-none" />
            </label>
            <label className="block">
              <div className="mb-2 text-xs uppercase tracking-[0.2em] text-white/35">Material</div>
              <input value={moldMaterial} onChange={(event) => setMoldMaterial(event.target.value)} className="h-12 w-full rounded-2xl border border-white/10 bg-black/10 px-4 text-sm text-white outline-none" />
            </label>
          </div>
          <div className="mt-4 text-xs text-white/40">
            Allowed range: {familyConfig.minWidth}-{familyConfig.maxWidth} mm width, {familyConfig.minHeight}-{familyConfig.maxHeight} mm height, {familyConfig.minThickness}-{familyConfig.maxThickness} mm thickness.
          </div>
        </SectionCard>
      );
    }

    if (["accounting", "socialmanager", "feedpublisher", "webbuilder", "cms"].includes(app.id)) {
      return (
        <EmptyPanel
          title="Inputs are saved through record workspaces"
          description="Use the Output tab to edit and persist records into project-backed JSON artifacts."
        />
      );
    }

    return (
      <SectionCard title="Inputs" description="Select the project and source file when the app operates on file-backed workflows.">
        <div className="grid gap-4 lg:grid-cols-2">
          <label className="block">
            <div className="mb-2 text-xs uppercase tracking-[0.2em] text-white/35">Project</div>
            <select value={selectedProject.id} onChange={(event) => setSelectedProjectId(event.target.value)} className="h-12 w-full rounded-2xl border border-white/10 bg-black/10 px-4 text-sm text-white outline-none">
              {projectOptions.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
          </label>
          <label className="block">
            <div className="mb-2 text-xs uppercase tracking-[0.2em] text-white/35">Source file</div>
            <select value={selectedFileId} onChange={(event) => setSelectedFileId(event.target.value)} className="h-12 w-full rounded-2xl border border-white/10 bg-black/10 px-4 text-sm text-white outline-none">
              <option value="">Select file</option>
              {relevantFiles.map((file) => (
                <option key={file.file_id} value={file.file_id}>
                  {file.original_filename}
                </option>
              ))}
            </select>
          </label>
        </div>
        {selectedFile ? (
          <div className="mt-4 rounded-[24px] border border-white/10 bg-black/10 p-4">
            <div className="text-sm font-semibold text-white">{selectedFile.original_filename}</div>
            <div className="mt-1 text-xs text-white/40">
              {selectedFile.kind} / {selectedFile.mode || "default"} / {selectedFile.status}
            </div>
          </div>
        ) : null}
      </SectionCard>
    );
  }

  function renderRun() {
    if (["accounting", "socialmanager", "feedpublisher", "webbuilder", "cms"].includes(app.id)) {
      return (
        <SectionCard title="Run" description="These MVP apps persist records directly; no worker execution is required.">
          <div className="text-sm text-white/55">Use the Output tab to create or update persisted records.</div>
        </SectionCard>
      );
    }
    return (
      <SectionCard title="Run" description="Only working actions are exposed.">
        <div className="flex flex-wrap gap-3">
          <button type="button" onClick={() => void onRun()} className="rounded-2xl bg-white px-5 py-3 text-sm font-medium text-black hover:bg-white/90">
            {["viewer3d", "viewer2d", "docviewer"].includes(app.id) ? "Open output" : "Run"}
          </button>
          {selectedFileId ? (
            <button type="button" onClick={() => void onCreateShare()} className="rounded-2xl border border-white/10 px-5 py-3 text-sm text-white/75 hover:bg-white/8">
              Create share
            </button>
          ) : null}
        </div>
        {shareUrl ? <div className="mt-4 rounded-[24px] border border-emerald-500/20 bg-emerald-500/8 px-4 py-3 text-sm text-emerald-100">{shareUrl}</div> : null}
        {error ? <div className="mt-4 text-sm text-red-200">{error}</div> : null}
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
          <div className="rounded-[24px] border border-white/10 bg-black/10 p-5">
            <div className="text-xs uppercase tracking-[0.2em] text-white/35">Job</div>
            <div className="mt-3 text-sm text-white">{job.job_id}</div>
            <div className="mt-2"><StatusBadge label={job.status} /></div>
            <div className="mt-3 text-xs text-white/40">Queued: {formatDate(job.enqueued_at)}</div>
            <div className="mt-1 text-xs text-white/40">Started: {formatDate(job.started_at)}</div>
            <div className="mt-1 text-xs text-white/40">Ended: {formatDate(job.ended_at)}</div>
          </div>
          <div className="rounded-[24px] border border-white/10 bg-black/10 p-5">
            <div className="text-xs uppercase tracking-[0.2em] text-white/35">Meta</div>
            <pre className="mt-3 overflow-x-auto whitespace-pre-wrap text-xs text-white/55">{JSON.stringify(job.meta || {}, null, 2)}</pre>
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
        <RecordWorkspace
          projectId={selectedProject.id}
          kind="social-account"
          title="Social Accounts"
          description="Connection metadata is storable; posting remains hidden without provider OAuth implementation."
          initialPayload={{ title: "Instagram account", network: "instagram", accountLabel: "", connectionState: "draft", owner: "", notes: "" }}
          fields={[
            { key: "title", label: "Title", type: "text", placeholder: "Instagram account" },
            { key: "network", label: "Network", type: "select", options: ["instagram", "linkedin", "x", "facebook"] },
            { key: "accountLabel", label: "Account Label", type: "text", placeholder: "@stellcodex" },
            { key: "connectionState", label: "Connection State", type: "select", options: ["draft", "pending", "connected"] },
            { key: "owner", label: "Owner", type: "text", placeholder: "Growth team" },
            { key: "notes", label: "Notes", type: "textarea", placeholder: "Posting hidden until OAuth is wired." },
          ]}
        />
      );
    }

    if (app.id === "feedpublisher") {
      return (
        <RecordWorkspace
          projectId={selectedProject.id}
          kind="feed-draft"
          title="Feed Publisher"
          description="Scheduler drafts and captions persist per project."
          initialPayload={{ title: "Launch post", channel: "instagram", publishAt: "", caption: "", assetFileId: selectedFileId }}
          fields={[
            { key: "title", label: "Title", type: "text", placeholder: "Launch post" },
            { key: "channel", label: "Channel", type: "select", options: ["instagram", "linkedin", "x", "facebook"] },
            { key: "publishAt", label: "Publish At", type: "date" },
            { key: "assetFileId", label: "Asset File Id", type: "text", placeholder: "Optional file_id" },
            { key: "caption", label: "Caption", type: "textarea", placeholder: "Write the post draft" },
          ]}
        />
      );
    }

    if (app.id === "webbuilder") {
      return (
        <RecordWorkspace
          projectId={selectedProject.id}
          kind="web-page"
          title="Web Builder"
          description="Create and save page drafts with real persistence."
          initialPayload={{ title: "Landing page", slug: "landing-page", headline: "", body: "", ctaLabel: "Contact sales" }}
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
          description="Slug, title and body content persist as editable drafts."
          initialPayload={{ title: "Knowledge article", slug: "knowledge-article", body: "", status: "draft" }}
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
              <div key={file.file_id} className="rounded-[20px] border border-white/10 bg-black/10 p-4">
                <div className="truncate text-sm font-semibold text-white">{file.original_filename}</div>
                <div className="mt-2 text-xs text-white/40">{file.kind} / {file.status}</div>
              </div>
            ))}
          </div>
        </SectionCard>
      );
    }

    if (app.id === "library") {
      return (
        <SectionCard title="Library Output" description="Open the full library route for publish and feed management.">
          <Link href="/library" className="rounded-2xl border border-white/10 px-5 py-3 text-sm text-white/75 hover:bg-white/8">
            Open library route
          </Link>
        </SectionCard>
      );
    }

    if (app.id === "projects") {
      return (
        <SectionCard title="Projects Output" description="Open the full projects route for project CRUD.">
          <Link href="/projects" className="rounded-2xl border border-white/10 px-5 py-3 text-sm text-white/75 hover:bg-white/8">
            Open projects route
          </Link>
        </SectionCard>
      );
    }

    if (app.id === "status" || app.id === "admin") {
      return (
        <SectionCard title="System Output" description="Use the admin route for release proof and health status.">
          <Link href="/admin" className="rounded-2xl border border-white/10 px-5 py-3 text-sm text-white/75 hover:bg-white/8">
            Open admin route
          </Link>
        </SectionCard>
      );
    }

    if ((["viewer3d", "viewer2d", "docviewer"].includes(app.id) && selectedFileId) || outputFileId) {
      const embeddedFileId = outputFileId || selectedFileId;
      return (
        <SectionCard title="Output" description="Embedded viewer plus download and deep-link actions.">
          <div className="overflow-hidden rounded-[28px] border border-white/10 bg-black/20">
            <iframe src={`/view/${embeddedFileId}`} className="h-[760px] w-full bg-[#111]" title="Embedded STELLCODEX output" />
          </div>
          <div className="mt-4 flex flex-wrap gap-3">
            <Link href={`/viewer/${embeddedFileId}`} className="rounded-2xl border border-white/10 px-5 py-3 text-sm text-white/75 hover:bg-white/8">
              Open deep link
            </Link>
            <button type="button" onClick={() => void onDownloadOutput(embeddedFileId)} className="rounded-2xl border border-white/10 px-5 py-3 text-sm text-white/75 hover:bg-white/8">
              Download output
            </button>
          </div>
        </SectionCard>
      );
    }

    return <EmptyPanel title="No output yet" description="Run the app or select a source file to populate output." />;
  }

  return (
    <PlatformLayout title={app.name} subtitle={app.summary}>
      <div className="mx-auto flex w-full max-w-[1480px] flex-col gap-6 px-4 py-6 lg:px-8">
        <div className="flex flex-wrap gap-2">
          {RUNNER_TABS.map((tab) => (
            <button
              key={tab}
              type="button"
              onClick={() => setActiveTab(tab)}
              className={`rounded-full px-4 py-2 text-sm ${
                activeTab === tab ? "bg-white text-black" : "border border-white/10 text-white/65 hover:bg-white/8"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {activeTab === "Overview" ? renderOverview() : null}
        {activeTab === "Inputs" ? renderInputs() : null}
        {activeTab === "Run" ? renderRun() : null}
        {activeTab === "Progress" ? renderProgress() : null}
        {activeTab === "Output" ? renderOutput() : null}
      </div>
    </PlatformLayout>
  );
}

export function PlatformClient({ view, appId = "", projectId = "", fileId = "" }: PlatformClientProps) {
  if (view === "home") return <HomeScreen />;
  if (view === "projects") return <ProjectsScreen />;
  if (view === "project") return <ProjectScreen projectId={projectId} />;
  if (view === "files") return <FilesScreen />;
  if (view === "library") return <LibraryScreen />;
  if (view === "settings") return <SettingsScreen />;
  if (view === "admin") return <AdminScreen />;
  if (view === "viewer") return <ViewerScreen fileId={fileId} />;
  return <AppRunnerScreen appId={appId} />;
}
