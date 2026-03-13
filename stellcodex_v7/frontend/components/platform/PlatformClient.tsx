"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useUser } from "@/context/UserContext";
import { getHomePlatformApps, getPlatformApp, type PlatformApp } from "@/data/platformCatalog";
import {
  getMarketplaceIntegration,
  resolveMarketplaceCoreAppId,
  summarizeMarketplaceCapabilities,
} from "@/data/platformMarketplace";
import { ensureSession } from "@/lib/sessionStore";
import { extractWorkspaceId, resolveFileAppPath, resolveWorkspaceHref } from "@/lib/workspace-routing";
import {
  createProject,
  createShare,
  enqueueConvert,
  enqueueMesh2d3d,
  enqueueMoldcodesExport,
  getAppManifest,
  getJob,
  getLibraryFeed,
  getProject,
  listAppsCatalog,
  listFiles,
  listProjects,
  uploadDirect,
  type AppsCatalogItem,
  type JobStatus,
  type LibraryItem,
  type ProjectSummary,
  type FileItem,
} from "@/services/api";
import { PlatformLayout } from "./PlatformLayout";

type PlatformView =
  | "home"
  | "apps"
  | "app"
  | "projects"
  | "project"
  | "files"
  | "library"
  | "settings"
  | "admin"
  | "viewer";

type PlatformClientProps = {
  view: PlatformView;
  appId?: string;
  projectId?: string;
  fileId?: string;
};

type MoldCategory = keyof typeof MOLD_CATALOG;

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

function formatDate(value?: string | null) {
  if (!value) return "No timestamp";
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

function formatBytes(value: number) {
  if (!Number.isFinite(value) || value <= 0) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const index = Math.min(Math.floor(Math.log(value) / Math.log(1024)), units.length - 1);
  const amount = value / 1024 ** index;
  return `${amount.toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

function titleCase(value: string) {
  return value
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function getFamilies(category: MoldCategory) {
  return Object.entries(MOLD_CATALOG[category].families);
}

export function PlatformClient({ view, appId, projectId, fileId }: PlatformClientProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { user } = useUser();
  const inputRef = useRef<HTMLInputElement | null>(null);
  const workspaceId = extractWorkspaceId(pathname) || ensureSession().id;

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [files, setFiles] = useState<FileItem[]>([]);
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [libraryItems, setLibraryItems] = useState<LibraryItem[]>([]);
  const [appsCatalog, setAppsCatalog] = useState<AppsCatalogItem[]>([]);
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  const [jobFileId, setJobFileId] = useState<string>("");
  const [projectName, setProjectName] = useState("");
  const [moduleManifest, setModuleManifest] = useState<Record<string, unknown> | null>(null);
  const [moldCategory, setMoldCategory] = useState<MoldCategory>("plates");
  const [moldFamily, setMoldFamily] = useState("base-a");
  const [moldWidth, setMoldWidth] = useState(120);
  const [moldHeight, setMoldHeight] = useState(160);
  const [moldThickness, setMoldThickness] = useState(24);

  useEffect(() => {
    void refreshWorkspace();
  }, [workspaceId]);

  useEffect(() => {
    if (jobFileId || files.length === 0) return;
    setJobFileId(fileId || files[0].file_id);
  }, [fileId, files, jobFileId]);

  useEffect(() => {
    const families = getFamilies(moldCategory);
    if (families.some(([key]) => key === moldFamily)) return;
    setMoldFamily(families[0]?.[0] || "");
  }, [moldCategory, moldFamily]);

  useEffect(() => {
    if (!appId) {
      setModuleManifest(null);
      return;
    }
    const manifestAppId = appId;
    if (getPlatformApp(manifestAppId)) {
      setModuleManifest(null);
      return;
    }

    let active = true;

    async function loadManifest() {
      try {
        const result = await getAppManifest(manifestAppId, true);
        if (active) setModuleManifest(result.manifest);
      } catch {
        if (active) setModuleManifest(null);
      }
    }

    void loadManifest();

    return () => {
      active = false;
    };
  }, [appId]);

  async function refreshWorkspace() {
    setLoading(true);
    setError(null);

    const [filesResult, projectsResult, appsResult, libraryResult] = await Promise.allSettled([
      listFiles(),
      listProjects(),
      listAppsCatalog(true),
      getLibraryFeed({ page_size: 6 }),
    ]);

    setFiles(filesResult.status === "fulfilled" ? filesResult.value : []);
    setProjects(projectsResult.status === "fulfilled" ? projectsResult.value : []);
    setAppsCatalog(appsResult.status === "fulfilled" ? appsResult.value : []);
    setLibraryItems(libraryResult.status === "fulfilled" ? libraryResult.value.items : []);

    if (
      filesResult.status === "rejected" ||
      projectsResult.status === "rejected" ||
      appsResult.status === "rejected" ||
      libraryResult.status === "rejected"
    ) {
      setError("Some workspace data could not be refreshed. The shell is still available.");
    }

    setLoading(false);
  }

  async function handleUpload(file: File) {
    setBusy("upload");
    setNotice(null);
    setError(null);

    try {
      const projectTarget = projectId || projects[0]?.id;
      const uploaded = await uploadDirect(file, projectTarget);
      const route = resolveFileAppPath(
        workspaceId,
        { original_filename: file.name, content_type: file.type },
        uploaded.file_id
      );
      setNotice(`Upload complete. Routed into ${route.appId}.`);
      router.push(route.href);
    } catch (err) {
      setError(err instanceof Error ? err.message : "The upload could not be completed.");
    } finally {
      setBusy(null);
    }
  }

  async function handleCreateProject() {
    if (!projectName.trim()) return;

    setBusy("project");
    setNotice(null);
    setError(null);

    try {
      const created = await createProject(projectName.trim());
      setProjectName("");
      setNotice(`Project created: ${created.name}`);
      await refreshWorkspace();
      router.push(resolveWorkspaceHref(workspaceId, `/projects/${created.id}`));
    } catch (err) {
      setError(err instanceof Error ? err.message : "The project could not be created.");
    } finally {
      setBusy(null);
    }
  }

  async function handleCreateShare(targetFileId: string) {
    setBusy(`share:${targetFileId}`);
    setNotice(null);
    setError(null);

    try {
      const share = await createShare(targetFileId, 7 * 24 * 60 * 60);
      setNotice(`Share created: /s/${share.token}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "The share link could not be created.");
    } finally {
      setBusy(null);
    }
  }

  async function handleRunJob(kind: "convert" | "mesh2d3d") {
    if (!jobFileId) return;

    setBusy(kind);
    setNotice(null);
    setError(null);

    try {
      const result = kind === "convert" ? await enqueueConvert(jobFileId) : await enqueueMesh2d3d(jobFileId);
      const refreshed = await getJob(result.job_id).catch(() => result);
      setJobStatus(refreshed);
      setNotice(`Job started: ${refreshed.job_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "The job could not be started.");
    } finally {
      setBusy(null);
    }
  }

  async function handleMoldcodesExport() {
    setBusy("moldcodes");
    setNotice(null);
    setError(null);

    try {
      const activeProject = projectId || projects[0]?.id || "default";
      const result = await enqueueMoldcodesExport({
        project_id: activeProject,
        category: moldCategory,
        family: moldFamily,
        params: {
          width: moldWidth,
          height: moldHeight,
          thickness: moldThickness,
        },
      });
      setJobStatus(result);
      setNotice(`MoldCodes export queued: ${result.job_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "The MoldCodes export could not be started.");
    } finally {
      setBusy(null);
    }
  }

  function openFileChooser() {
    inputRef.current?.click();
  }

  function HomeScreen() {
    const focusApps = getHomePlatformApps(user.role).slice(0, 6);

    return (
      <section className="workspace-section">
        <div className="hero-grid">
          <div className="hero-card">
            <div className="eyebrow">Suite home</div>
            <h2 className="display-title">Simple in front. Specialized underneath.</h2>
            <p className="lede">
              STELLCODEX is one calm shell for industrial files, projects, and focused applications. Upload once. Open the right app automatically.
            </p>
            <div className="hero-actions">
              <button className="button button--primary" type="button" onClick={openFileChooser}>
                Select file
              </button>
              <Link className="button button--ghost" href={resolveWorkspaceHref(workspaceId, "/files")}>
                Open Files and Share
              </Link>
              <Link className="button button--ghost" href={resolveWorkspaceHref(workspaceId, "/apps")}>
                Browse all applications
              </Link>
            </div>
            <div className="pill-row">
              <span className="pill">No cloned entry pages</span>
              <span className="pill">Shared suite identity</span>
            </div>
          </div>

          <div className="panel-grid">
            <div className="surface-card">
              <h3>3D workspace</h3>
              <p className="page-copy">STEP, STL, and GLB files route into the focused 3D review flow.</p>
            </div>
            <div className="surface-card">
              <h3>2D workspace</h3>
              <p className="page-copy">DXF drawings stay in a lighter, layer-aware review surface.</p>
            </div>
            <div className="surface-card">
              <h3>document workspace</h3>
              <p className="page-copy">PDF and document files stay readable and low-friction.</p>
            </div>
          </div>
        </div>

        <div className="stat-grid">
          <div className="metric-card">
            <div className="muted">Files</div>
            <div className="metric-value">{files.length}</div>
          </div>
          <div className="metric-card">
            <div className="muted">Projects</div>
            <div className="metric-value">{projects.length}</div>
          </div>
          <div className="metric-card">
            <div className="muted">Applications</div>
            <div className="metric-value">{focusApps.length}</div>
          </div>
        </div>

        <div className="card-grid">
          {focusApps.map((app) => (
            <Link key={app.id} className="surface-card" href={resolveWorkspaceHref(workspaceId, app.route)}>
              <h3>{app.name}</h3>
              <p className="page-copy">{app.summary}</p>
              <span className="status-chip">{app.surface}</span>
            </Link>
          ))}
        </div>
      </section>
    );
  }

  function AppsCatalogScreen() {
    const enabledCount = appsCatalog.filter((item) => item.enabled).length;

    return (
      <section className="workspace-section">
        <div className="page-head">
          <div>
            <h2 className="page-title">Applications catalog</h2>
            <p className="page-copy">Inventory Status</p>
          </div>
          <button className="button button--ghost" type="button" onClick={() => void refreshWorkspace()}>
            Refresh inventory
          </button>
        </div>

        <div className="stat-grid">
          <div className="metric-card">
            <div className="muted">Core apps</div>
            <div className="metric-value">{getHomePlatformApps(user.role).length}</div>
          </div>
          <div className="metric-card">
            <div className="muted">Marketplace rows</div>
            <div className="metric-value">{appsCatalog.length}</div>
          </div>
          <div className="metric-card">
            <div className="muted">Enabled now</div>
            <div className="metric-value">{enabledCount}</div>
          </div>
        </div>

        <div className="card-grid">
          {getHomePlatformApps(user.role).map((app) => (
            <Link key={app.id} className="surface-card" href={resolveWorkspaceHref(workspaceId, app.route)}>
              <h3>{app.name}</h3>
              <p className="page-copy">{app.description}</p>
              <div className="pill-row">
                <span className="pill">{app.category}</span>
                <span className="pill">{app.surface}</span>
              </div>
            </Link>
          ))}
        </div>

        {appsCatalog.length > 0 ? (
          <div className="list">
            {appsCatalog.slice(0, 12).map((item) => (
              <Link key={item.slug} className="list-item" href={resolveWorkspaceHref(workspaceId, `/app/${item.slug}`)}>
                <div>
                  <strong>{item.name}</strong>
                  <div className="list-item-meta">
                    <span>{titleCase(item.category)}</span>
                    <span>{item.tier}</span>
                    <span>{item.enabled ? "enabled" : "disabled"}</span>
                  </div>
                </div>
                <span className="status-chip">{item.slug}</span>
              </Link>
            ))}
          </div>
        ) : null}
      </section>
    );
  }

  function FilesScreen() {
    return (
      <section className="workspace-section">
        <div className="page-head">
          <div>
            <h2 className="page-title">Files</h2>
            <p className="page-copy">File Ledger</p>
          </div>
          <button className="button button--primary" type="button" onClick={openFileChooser}>
            Upload file
          </button>
        </div>

        <div className="list">
          {files.map((file) => (
            <div key={file.file_id} className="list-item">
              <div>
                <strong>{file.original_name}</strong>
                <div className="list-item-meta">
                  <span>{file.kind}</span>
                  <span>{formatBytes(file.size_bytes)}</span>
                  <span>{formatDate(file.created_at)}</span>
                </div>
              </div>
              <div className="hero-actions" style={{ marginTop: 0 }}>
                <Link className="button button--ghost" href={resolveWorkspaceHref(workspaceId, `/open/${file.file_id}`)}>
                  Open
                </Link>
                <button className="button button--ghost" type="button" onClick={() => void handleCreateShare(file.file_id)}>
                  {busy === `share:${file.file_id}` ? "Creating..." : "Create share"}
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>
    );
  }

  function ProjectsScreen() {
    return (
      <section className="workspace-section">
        <div className="page-head">
          <div>
            <h2 className="page-title">Projects</h2>
            <p className="page-copy">Project Index</p>
          </div>
        </div>

        <div className="panel-grid">
          <div className="panel">
            <h3>Create Project</h3>
            <div className="auth-form">
              <input
                className="field"
                value={projectName}
                placeholder="Injection mold v2"
                onChange={(event) => setProjectName(event.target.value)}
              />
              <button className="button button--primary" type="button" onClick={() => void handleCreateProject()}>
                {busy === "project" ? "Creating..." : "Create project"}
              </button>
            </div>
          </div>

          <div className="panel">
            <h3>Linked files</h3>
            <p className="page-copy">
              Projects stay close to upload routing so files can open in the right application without a second shell.
            </p>
          </div>
        </div>

        <div className="list">
          {projects.map((project) => (
            <Link key={project.id} className="list-item" href={resolveWorkspaceHref(workspaceId, `/projects/${project.id}`)}>
              <div>
                <strong>{project.name}</strong>
                <div className="list-item-meta">
                  <span>{project.file_count} files</span>
                  <span>{formatDate(project.updated_at)}</span>
                </div>
              </div>
              <span className="status-chip">{project.id}</span>
            </Link>
          ))}
        </div>
      </section>
    );
  }

  function ProjectDetailScreen() {
    const project = projects.find((item) => item.id === projectId);

    return (
      <section className="workspace-section">
        <div className="page-head">
          <div>
            <h2 className="page-title">{project?.name || "Project detail"}</h2>
            <p className="page-copy">Files, links, and app routing stay attached to the project scope.</p>
          </div>
          <Link className="button button--ghost" href={resolveWorkspaceHref(workspaceId, "/projects")}>
            Back to projects
          </Link>
        </div>

        <div className="panel">
          <h3>Current state</h3>
          <p className="page-copy">
            {project ? `${project.file_count} files are attached to this project.` : "This project was not found in the current client snapshot."}
          </p>
        </div>
      </section>
    );
  }

  function LibraryScreen() {
    return (
      <section className="workspace-section">
        <div className="page-head">
          <div>
            <h2 className="page-title">Library</h2>
            <p className="page-copy">Library Output</p>
          </div>
          <button className="button button--ghost" type="button" onClick={() => void refreshWorkspace()}>
            Refresh feed
          </button>
        </div>

        <div className="panel">
          <h3>Publishing rule</h3>
          <p className="page-copy">Open the full library route for publish and feed management.</p>
        </div>

        <div className="list">
          {libraryItems.map((item) => (
            <div key={item.id} className="list-item">
              <div>
                <strong>{item.title}</strong>
                <div className="list-item-meta">
                  <span>{item.visibility}</span>
                  <span>{item.tags.join(", ") || "No tags"}</span>
                </div>
              </div>
              {item.share_url ? (
                <a className="button button--ghost" href={item.share_url} target="_blank" rel="noreferrer">
                  Open share
                </a>
              ) : null}
            </div>
          ))}
        </div>
      </section>
    );
  }

  function SettingsScreen() {
    return (
      <section className="workspace-section">
        <div className="page-head">
          <div>
            <h2 className="page-title">Plan access</h2>
            <p className="page-copy">Suite access stays under one product identity.</p>
          </div>
        </div>

        <div className="card-grid">
          {SUITE_PLAN_ROWS.map((plan) => (
            <div key={plan.name} className="surface-card">
              <div className="eyebrow">{plan.name}</div>
              <h3>{plan.headline}</h3>
              <p className="page-copy">{plan.description}</p>
            </div>
          ))}
        </div>
      </section>
    );
  }

  function AdminScreen() {
    return (
      <section className="workspace-section">
        <div className="page-head">
          <div>
            <h2 className="page-title">Admin</h2>
            <p className="page-copy">Audit, release evidence, and system access stay inside the shared shell.</p>
          </div>
        </div>

        <div className="stat-grid">
          <div className="metric-card">
            <div className="muted">Files visible</div>
            <div className="metric-value">{files.length}</div>
          </div>
          <div className="metric-card">
            <div className="muted">Projects visible</div>
            <div className="metric-value">{projects.length}</div>
          </div>
          <div className="metric-card">
            <div className="muted">Inventory rows</div>
            <div className="metric-value">{appsCatalog.length}</div>
          </div>
        </div>
      </section>
    );
  }

  function ViewerScreen() {
    const activeFile = files.find((item) => item.file_id === fileId) || null;

    return (
      <section className="workspace-section">
        <div className="page-head">
          <div>
            <h2 className="page-title">{activeFile?.original_name || "Viewer"}</h2>
            <p className="page-copy">Focused file review stays separate from the catalog and suite services.</p>
          </div>
          {fileId ? (
            <Link className="button button--ghost" href={`/view/${fileId}`}>
              Open standalone viewer
            </Link>
          ) : null}
        </div>

        <div className="panel">
          <h3>Current file</h3>
          <p className="page-copy">
            {activeFile
              ? `${activeFile.kind} file, ${formatBytes(activeFile.size_bytes)}, status ${activeFile.status}.`
              : "Select a file from the Files surface to continue into a focused viewer."}
          </p>
        </div>
      </section>
    );
  }

  function AppScreen() {
    const aliasId = appId ? resolveMarketplaceCoreAppId(appId) : null;
    const app = getPlatformApp(aliasId || appId || "");
    const manifestItem = appId ? appsCatalog.find((item) => item.slug === appId) || null : null;

    if (!app && manifestItem) {
      return <MarketplaceModuleScreen item={manifestItem} manifest={moduleManifest} />;
    }

    if (!app) {
      return (
        <section className="workspace-section">
          <div className="panel">
            <h3>Application not found</h3>
            <p className="page-copy">The requested application is not registered in the current workspace inventory.</p>
          </div>
        </section>
      );
    }

    const currentApp: PlatformApp = app;
    const surface = app.surface;
    const familyConfig = (MOLD_CATALOG[moldCategory].families as Record<string, { label: string; minWidth: number; maxWidth: number; minHeight: number; maxHeight: number; minThickness: number; maxThickness: number }>)[moldFamily];

    function renderCatalogSurface() {
      return <AppsCatalogScreen />;
    }

    function renderViewerSurface() {
      return (
        <section className="workspace-section">
          <div className="page-head">
            <div>
              <h2 className="page-title">{currentApp.name}</h2>
              <p className="page-copy">{currentApp.summary}</p>
            </div>
          </div>
          <div className="panel">
            <h3>{currentApp.surface === "viewer2d" ? "2D workspace" : currentApp.surface === "docviewer" ? "document workspace" : "3D workspace"}</h3>
            <p className="page-copy">Choose a file from the ledger or upload directly from the suite home.</p>
          </div>
        </section>
      );
    }

    function renderJobSurface() {
      return (
        <section className="workspace-section">
          <div className="page-head">
            <div>
              <h2 className="page-title">{currentApp.name}</h2>
              <p className="page-copy">Only working actions are exposed.</p>
            </div>
          </div>
          <div className="panel-grid">
            <div className="panel">
              <h3>Source File</h3>
              <select className="select" value={jobFileId} onChange={(event) => setJobFileId(event.target.value)}>
                {files.map((file) => (
                  <option key={file.file_id} value={file.file_id}>
                    {file.original_name}
                  </option>
                ))}
              </select>
              <div className="hero-actions">
                <button
                  className="button button--primary"
                  type="button"
                  onClick={() => void handleRunJob(currentApp.id === "convert" ? "convert" : "mesh2d3d")}
                >
                  {busy === currentApp.id ? "Starting..." : "Start job"}
                </button>
              </div>
            </div>
            <div className="panel">
              <h3>Last run</h3>
              <p className="page-copy">
                {jobStatus ? `${jobStatus.job_id} is ${jobStatus.status}.` : "No queued job in this local session yet."}
              </p>
            </div>
          </div>
        </section>
      );
    }

    function renderConfiguratorSurface() {
      return (
        <section className="workspace-section">
          <div className="page-head">
            <div>
              <h2 className="page-title">{currentApp.name}</h2>
              <p className="page-copy">Category, family and validated dimensions feed the export job.</p>
            </div>
          </div>
          <div className="panel-grid">
            <div className="panel">
              <h3>Configuration</h3>
              <div className="auth-form">
                <label>
                  <div className="muted">Category</div>
                  <select className="select" value={moldCategory} onChange={(event) => setMoldCategory(event.target.value as MoldCategory)}>
                    {Object.entries(MOLD_CATALOG).map(([key, value]) => (
                      <option key={key} value={key}>
                        {value.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  <div className="muted">Family</div>
                  <select className="select" value={moldFamily} onChange={(event) => setMoldFamily(event.target.value)}>
                    {getFamilies(moldCategory).map(([key, family]) => (
                      <option key={key} value={key}>
                        {family.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  <div className="muted">Width</div>
                  <input className="field" type="number" value={moldWidth} onChange={(event) => setMoldWidth(Number(event.target.value))} />
                </label>
                <label>
                  <div className="muted">Height</div>
                  <input className="field" type="number" value={moldHeight} onChange={(event) => setMoldHeight(Number(event.target.value))} />
                </label>
                <label>
                  <div className="muted">Thickness</div>
                  <input
                    className="field"
                    type="number"
                    value={moldThickness}
                    onChange={(event) => setMoldThickness(Number(event.target.value))}
                  />
                </label>
                <button className="button button--primary" type="button" onClick={() => void handleMoldcodesExport()}>
                  {busy === "moldcodes" ? "Queueing..." : "Queue export"}
                </button>
              </div>
            </div>
            <div className="panel">
              <h3>Validation</h3>
              <p className="page-copy">
                Allowed range: {familyConfig.minWidth} to {familyConfig.maxWidth} width, {familyConfig.minHeight} to {familyConfig.maxHeight} height, {familyConfig.minThickness} to {familyConfig.maxThickness} thickness.
              </p>
            </div>
          </div>
        </section>
      );
    }

    function renderRecordSurface() {
      return (
        <section className="workspace-section">
          <div className="page-head">
            <div>
              <h2 className="page-title">{currentApp.name}</h2>
              <p className="page-copy">{currentApp.summary}</p>
            </div>
          </div>
          <div className="panel">
            <h3>Focused records surface</h3>
            <p className="page-copy">
              This module stays intentionally narrow. The suite shell keeps the entry flow stable while the app owns its own record logic.
            </p>
          </div>
        </section>
      );
    }

    function renderRouteSurface() {
      const destination =
        currentApp.id === "library"
          ? "/library"
          : currentApp.id === "drive"
          ? "/files"
          : currentApp.id === "projects"
          ? "/projects"
          : currentApp.id === "admin" || currentApp.id === "status"
          ? "/admin"
          : currentApp.route;

      return (
        <section className="workspace-section">
          <div className="page-head">
            <div>
              <h2 className="page-title">{currentApp.name}</h2>
              <p className="page-copy">{currentApp.description}</p>
            </div>
          </div>
          <div className="panel">
            <h3>Route surface</h3>
            <p className="page-copy">
              This application resolves into a canonical suite route instead of opening a second interface.
            </p>
            <div className="hero-actions">
              <Link className="button button--primary" href={resolveWorkspaceHref(workspaceId, destination)}>
                Open route
              </Link>
            </div>
          </div>
        </section>
      );
    }

    if (surface === "catalog") return renderCatalogSurface();
    if (surface === "viewer3d" || surface === "viewer2d" || surface === "docviewer") return renderViewerSurface();
    if (surface === "job") return renderJobSurface();
    if (surface === "configurator") return renderConfiguratorSurface();
    if (surface === "records") return renderRecordSurface();
    return renderRouteSurface();
  }

  function renderBody() {
    if (view === "home") return <HomeScreen />;
    if (view === "apps") return <AppsCatalogScreen />;
    if (view === "files") return <FilesScreen />;
    if (view === "projects") return <ProjectsScreen />;
    if (view === "project") return <ProjectDetailScreen />;
    if (view === "library") return <LibraryScreen />;
    if (view === "settings") return <SettingsScreen />;
    if (view === "admin") return <AdminScreen />;
    if (view === "viewer") return <ViewerScreen />;
    return <AppScreen />;
  }

  const title =
    view === "app"
      ? getPlatformApp(resolveMarketplaceCoreAppId(appId || "") || appId || "")?.name || titleCase(appId || "Application")
      : view === "project"
      ? "Project detail"
      : titleCase(view);
  const subtitle =
    view === "home"
      ? "One product. Focused surfaces inside it."
      : view === "files"
      ? "Upload, share, and route files without opening a second shell."
      : view === "projects"
      ? "Projects stay linked to suite-wide file routing."
      : "Calm, canonical suite surface.";

  return (
    <PlatformLayout title={title} subtitle={subtitle}>
      <input
        ref={inputRef}
        className="hidden-input"
        type="file"
        onChange={(event) => {
          const file = event.target.files?.[0];
          if (file) void handleUpload(file);
          event.currentTarget.value = "";
        }}
      />

      {notice ? (
        <div className="panel" style={{ marginBottom: "1rem" }}>
          <div className="status-chip">{notice}</div>
        </div>
      ) : null}

      {error ? (
        <div className="panel" style={{ marginBottom: "1rem" }}>
          <span className="status-chip" data-tone="danger">
            {error}
          </span>
        </div>
      ) : null}

      {loading ? <div className="panel">Refreshing the current workspace surface.</div> : renderBody()}
    </PlatformLayout>
  );
}

function MarketplaceModuleScreen({
  item,
  manifest,
}: {
  item: AppsCatalogItem;
  manifest: Record<string, unknown> | null;
}) {
  const integration = getMarketplaceIntegration(item);
  const summary = summarizeMarketplaceCapabilities(item);

  return (
    <section className="workspace-section">
      <div className="page-head">
        <div>
          <h2 className="page-title">{item.name}</h2>
          <p className="page-copy">{integration.headline}</p>
        </div>
      </div>

      <div className="panel-grid">
        <div className="panel">
          <h3>Module status</h3>
          <p className="page-copy">{integration.note}</p>
          <div className="pill-row">
            <span className="pill">{item.enabled ? "enabled" : "disabled"}</span>
            <span className="pill">{item.tier}</span>
          </div>
        </div>
        <div className="panel">
          <h3>Capabilities</h3>
          <p className="page-copy">{summary.capabilities}</p>
          <p className="page-copy">{summary.formats}</p>
        </div>
      </div>

      <div className="panel">
        <h3>Manifest snapshot</h3>
        <pre style={{ margin: 0, whiteSpace: "pre-wrap" }}>
          {JSON.stringify(manifest || { slug: item.slug, routes: item.routes }, null, 2)}
        </pre>
      </div>
    </section>
  );
}
