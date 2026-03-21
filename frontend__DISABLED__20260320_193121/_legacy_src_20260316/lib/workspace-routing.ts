export type FileLike = {
  original_filename?: string | null;
  content_type?: string | null;
};

export type WorkspaceAppRoute = "viewer3d" | "viewer2d" | "docviewer";

const DOC_EXTENSIONS = [
  ".pdf",
  ".doc",
  ".docx",
  ".xlsx",
  ".pptx",
  ".odt",
  ".ods",
  ".odp",
  ".rtf",
  ".txt",
  ".csv",
  ".html",
  ".htm",
  ".zip",
  ".rar",
  ".7z",
] as const;

const DOC_CONTENT_TYPES = [
  "application/pdf",
  "application/msword",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "application/vnd.openxmlformats-officedocument.presentationml.presentation",
  "application/vnd.oasis.opendocument.text",
  "application/vnd.oasis.opendocument.spreadsheet",
  "application/vnd.oasis.opendocument.presentation",
  "application/rtf",
  "text/plain",
  "text/csv",
  "text/html",
  "application/zip",
  "application/x-zip-compressed",
  "application/vnd.rar",
  "application/x-rar-compressed",
  "application/x-7z-compressed",
] as const;

function splitHref(href: string) {
  const [pathAndSearch, hash = ""] = href.split("#", 2);
  const [path, search = ""] = pathAndSearch.split("?", 2);
  return { path, search, hash };
}

function joinHref(path: string, search = "", hash = "") {
  const query = search ? `?${search}` : "";
  const fragment = hash ? `#${hash}` : "";
  return `${path}${query}${fragment}`;
}

export function buildWorkspacePath(workspaceId: string, suffix = "") {
  const normalized = suffix
    ? suffix.startsWith("/")
      ? suffix
      : `/${suffix}`
    : "";
  return `/workspace/${encodeURIComponent(workspaceId)}${normalized}`;
}

export function buildWorkspaceAppPath(workspaceId: string, appId: string, fileId?: string | null) {
  const base = buildWorkspacePath(workspaceId, `/app/${encodeURIComponent(appId)}`);
  return fileId ? `${base}?file_id=${encodeURIComponent(fileId)}` : base;
}

export function buildStandaloneViewerPath(fileId: string) {
  return `/view/${encodeURIComponent(fileId)}`;
}

export function extractWorkspaceId(pathname: string | null | undefined) {
  if (!pathname) return null;
  const match = pathname.match(/^\/workspace\/([^/]+)/);
  return match ? decodeURIComponent(match[1]) : null;
}

function isDocumentLike(name: string, contentType: string) {
  if (contentType.startsWith("image/")) return true;
  if (DOC_CONTENT_TYPES.includes(contentType as (typeof DOC_CONTENT_TYPES)[number])) return true;
  return DOC_EXTENSIONS.some((ext) => name.endsWith(ext));
}

export function classifyWorkspaceApp(file: FileLike | null | undefined) {
  const name = (file?.original_filename || "").toLowerCase();
  const contentType = (file?.content_type || "").toLowerCase();

  if (name.endsWith(".dxf")) return "viewer2d" as const;
  if (isDocumentLike(name, contentType)) return "docviewer" as const;
  return "viewer3d" as const;
}

export function buildFileAppPath(appId: WorkspaceAppRoute, fileId: string) {
  return `/app/${encodeURIComponent(appId)}?file_id=${encodeURIComponent(fileId)}`;
}

export function resolveFileAppPath(workspaceId: string | null | undefined, file: FileLike | null | undefined, fileId: string) {
  // Uploads should land in the focused app surface, not a generic catch-all page.
  const appId = classifyWorkspaceApp(file);
  return {
    appId,
    href: workspaceId ? buildWorkspaceAppPath(workspaceId, appId, fileId) : buildFileAppPath(appId, fileId),
  };
}

export function buildWorkspaceOpenPath(workspaceId: string, fileId: string) {
  return buildWorkspacePath(workspaceId, `/open/${encodeURIComponent(fileId)}`);
}

export function buildWorkspaceConvertPath(workspaceId: string, fileId?: string | null) {
  return fileId
    ? buildWorkspacePath(workspaceId, `/convert/${encodeURIComponent(fileId)}`)
    : buildWorkspacePath(workspaceId, "/convert");
}

export function buildWorkspaceProjectPath(workspaceId: string, projectId: string) {
  return buildWorkspacePath(workspaceId, `/projects/${encodeURIComponent(projectId)}`);
}

export function resolveWorkspaceHref(workspaceId: string | null | undefined, href: string) {
  if (!workspaceId || !href.startsWith("/")) return href;

  const { path, search, hash } = splitHref(href);

  if (path === "/" || path === "") return joinHref(buildWorkspacePath(workspaceId), search, hash);
  if (path.startsWith("/workspace/")) return href;
  if (path.startsWith("/view/") || path.startsWith("/s/")) return href;
  if (path.startsWith("/viewer/")) {
    const fileId = path.slice("/viewer/".length);
    return joinHref(buildWorkspaceOpenPath(workspaceId, fileId), search, hash);
  }
  if (path.startsWith("/project/")) {
    const projectId = path.slice("/project/".length);
    return joinHref(buildWorkspaceProjectPath(workspaceId, projectId), search, hash);
  }
  if (path.startsWith("/app/")) {
    const appId = path.slice("/app/".length);
    const fileId = new URLSearchParams(search).get("file_id");
    return joinHref(buildWorkspaceAppPath(workspaceId, appId, fileId), "", hash);
  }
  if (path === "/apps") {
    return joinHref(buildWorkspacePath(workspaceId, "/apps"), search, hash);
  }
  if (path.startsWith("/apps/")) {
    const slug = path.slice("/apps/".length);
    return joinHref(buildWorkspaceAppPath(workspaceId, slug), "", hash);
  }
  if (path === "/projects" || path.startsWith("/projects/")) {
    return joinHref(buildWorkspacePath(workspaceId, path), search, hash);
  }
  if (path === "/files" || path === "/library" || path === "/settings" || path === "/admin") {
    return joinHref(buildWorkspacePath(workspaceId, path), search, hash);
  }

  return joinHref(buildWorkspacePath(workspaceId, path), search, hash);
}

export function resolveLegacyAppPath(workspaceId: string, appId: string, fileId?: string | null) {
  if (appId === "convert") return buildWorkspaceConvertPath(workspaceId, fileId);
  if (["viewer3d", "viewer2d", "docviewer"].includes(appId) && fileId) {
    return buildWorkspaceOpenPath(workspaceId, fileId);
  }
  if (appId === "library") return buildWorkspacePath(workspaceId, "/library");
  if (appId === "drive") return buildWorkspacePath(workspaceId, "/files");
  if (appId === "projects") return buildWorkspacePath(workspaceId, "/projects");
  if (appId === "status" || appId === "admin") return "/admin";
  return buildWorkspacePath(workspaceId);
}
