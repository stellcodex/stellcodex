const API_BASE_FALLBACK = "http://127.0.0.1:8000/api/v1";

export function apiBase() {
  return (
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    process.env.NEXT_PUBLIC_API_BASE ||
    API_BASE_FALLBACK
  ).replace(/\/+$/, "");
}

function parseCookies(cookieHeader: string): Record<string, string> {
  const out: Record<string, string> = {};
  for (const part of cookieHeader.split(";")) {
    const [rawKey, ...rawVal] = part.trim().split("=");
    if (!rawKey) continue;
    out[rawKey] = decodeURIComponent(rawVal.join("=") || "");
  }
  return out;
}

export function bearerFromRequest(req: Request): string | null {
  const direct = (req.headers.get("authorization") || "").trim();
  if (direct) return direct;

  const cookies = parseCookies(req.headers.get("cookie") || "");
  const token = (cookies.scx_token || cookies.stellcodex_access_token || "").trim();
  if (!token) return null;
  return `Bearer ${token}`;
}

export function upstreamHeaders(req: Request, extra?: HeadersInit): Headers {
  const headers = new Headers(extra || {});
  const bearer = bearerFromRequest(req);
  if (bearer && !headers.has("Authorization")) {
    headers.set("Authorization", bearer);
  }
  return headers;
}

export async function readPayload(response: Response): Promise<unknown> {
  const text = await response.text().catch(() => "");
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

export function readErrorMessage(payload: unknown, fallback: string): string {
  if (!payload) return fallback;
  if (typeof payload === "string") return payload || fallback;
  if (typeof payload !== "object") return fallback;
  if ("error" in payload && typeof (payload as { error?: unknown }).error === "string") {
    return ((payload as { error: string }).error || "").trim() || fallback;
  }
  if ("detail" in payload) {
    const detail = (payload as { detail?: unknown }).detail;
    if (typeof detail === "string" && detail.trim()) return detail;
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0];
      if (typeof first === "string" && first.trim()) return first;
      if (typeof first === "object" && first !== null) {
        const msg = (first as { msg?: unknown }).msg;
        if (typeof msg === "string" && msg.trim()) return msg;
      }
    }
  }
  return fallback;
}

export function extOf(filename: string): string {
  return (filename.split(".").pop() || "").toLowerCase();
}

export type LegacyFileKind = "3d" | "2d" | "pdf" | "image" | "office" | "zip" | "unknown";
export type LegacyEngine = "viewer3d" | "viewer2d" | "pdf" | "image" | "office" | "archive" | "unsupported";
export type LegacyJobStage = "uploaded" | "security" | "preview" | "ready";
export type LegacyJobStatus = "CREATED" | "RUNNING" | "SUCCEEDED" | "FAILED" | "NEEDS_APPROVAL";

function isArchiveExt(ext: string) {
  return ext === "zip" || ext === "rar" || ext === "7z";
}

export function mapLegacyKind(kindRaw: unknown, contentTypeRaw: unknown, filenameRaw: unknown): LegacyFileKind {
  const kind = typeof kindRaw === "string" ? kindRaw.toLowerCase() : "";
  const contentType = typeof contentTypeRaw === "string" ? contentTypeRaw.toLowerCase() : "";
  const filename = typeof filenameRaw === "string" ? filenameRaw : "";
  const ext = extOf(filename);

  if (kind === "archive" || isArchiveExt(ext)) return "zip";
  if (kind === "2d") return "2d";
  if (kind === "3d") return "3d";
  if (kind === "image" || contentType.startsWith("image/")) return "image";
  if (kind === "doc" || contentType === "application/pdf" || contentType.startsWith("text/")) {
    return ext === "pdf" || contentType === "application/pdf" ? "pdf" : "office";
  }

  if (ext === "dxf" || ext === "dwg" || ext === "svg") return "2d";
  if (ext === "pdf") return "pdf";
  if (["txt", "md", "doc", "docx", "xlsx", "csv", "rtf", "odt", "ods", "odp", "pptx"].includes(ext)) return "office";
  if (["jpg", "jpeg", "png", "webp", "gif", "bmp", "tif", "tiff"].includes(ext)) return "image";
  if (["step", "stp", "iges", "igs", "stl", "obj", "ply", "glb", "gltf", "x_t", "x_b"].includes(ext)) return "3d";
  return "unknown";
}

export function mapLegacyEngine(kindRaw: unknown, contentTypeRaw: unknown, filenameRaw: unknown): LegacyEngine {
  const kind = mapLegacyKind(kindRaw, contentTypeRaw, filenameRaw);
  if (kind === "3d") return "viewer3d";
  if (kind === "2d") return "viewer2d";
  if (kind === "pdf") return "pdf";
  if (kind === "image") return "image";
  if (kind === "office") return "office";
  if (kind === "zip") return "archive";
  return "unsupported";
}

export function mapLegacyStatusFromState(rawState: unknown): LegacyJobStatus {
  const state = typeof rawState === "string" ? rawState.toLowerCase() : "";
  if (state === "failed") return "FAILED";
  if (state === "succeeded" || state === "ready") return "SUCCEEDED";
  if (state === "running" || state === "processing") return "RUNNING";
  return "CREATED";
}

export function mapLegacyStatusFromJob(rawStatus: unknown): LegacyJobStatus {
  const status = typeof rawStatus === "string" ? rawStatus.toLowerCase() : "";
  if (status === "failed") return "FAILED";
  if (status === "finished" || status === "succeeded") return "SUCCEEDED";
  if (status === "started" || status === "running" || status === "processing") return "RUNNING";
  return "CREATED";
}

export function mapLegacyStage(rawStage: unknown, rawState: unknown): LegacyJobStage {
  const stage = typeof rawStage === "string" ? rawStage.toLowerCase() : "";
  const state = typeof rawState === "string" ? rawState.toLowerCase() : "";

  if (state === "succeeded" || state === "ready" || stage.includes("ready")) return "ready";
  if (stage.includes("security") || stage.includes("scan")) return "security";
  if (stage.includes("queue") || stage.includes("upload")) return "uploaded";
  if (stage.includes("convert") || stage.includes("pipeline") || stage.includes("preview") || stage.includes("process")) {
    return "preview";
  }
  if (state === "running") return "preview";
  if (state === "failed") return "preview";
  return "uploaded";
}

export function mapLegacyProgress(rawProgress: unknown, rawState: unknown): number {
  if (typeof rawProgress === "number" && Number.isFinite(rawProgress)) {
    return Math.max(0, Math.min(100, Math.round(rawProgress)));
  }
  const state = typeof rawState === "string" ? rawState.toLowerCase() : "";
  if (state === "succeeded" || state === "ready" || state === "failed") return 100;
  if (state === "running") return 55;
  return 5;
}
