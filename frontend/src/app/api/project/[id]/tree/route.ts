import { NextResponse } from "next/server";
import {
  apiBase,
  extOf,
  mapLegacyEngine,
  mapLegacyKind,
  readErrorMessage,
  readPayload,
  upstreamHeaders,
} from "@/app/api/_lib/upstream";

function mimeFromExt(ext: string) {
  if (ext === "pdf") return "application/pdf";
  if (ext === "txt") return "text/plain";
  if (ext === "md") return "text/markdown";
  if (ext === "csv") return "text/csv";
  if (["jpg", "jpeg"].includes(ext)) return "image/jpeg";
  if (ext === "png") return "image/png";
  if (ext === "webp") return "image/webp";
  if (ext === "svg") return "image/svg+xml";
  if (ext === "zip") return "application/zip";
  if (ext === "rar") return "application/x-rar-compressed";
  if (ext === "7z") return "application/x-7z-compressed";
  if (ext === "dxf") return "image/vnd.dxf";
  if (ext === "dwg") return "image/vnd.dwg";
  if (["step", "stp"].includes(ext)) return "model/step";
  if (ext === "stl") return "model/stl";
  if (ext === "obj") return "model/obj";
  if (ext === "gltf") return "model/gltf+json";
  if (ext === "glb") return "model/gltf-binary";
  if (ext === "docx") return "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
  if (ext === "xlsx") return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
  if (ext === "pptx") return "application/vnd.openxmlformats-officedocument.presentationml.presentation";
  return "application/octet-stream";
}

function mapFileRecord(input: Record<string, unknown>, projectId: string, folderId: string) {
  const name =
    typeof input.name === "string" && input.name.trim()
      ? input.name
      : typeof input.original_filename === "string" && input.original_filename.trim()
      ? input.original_filename
      : "unnamed";
  const ext = typeof input.ext === "string" && input.ext.trim() ? input.ext.toLowerCase() : extOf(name);
  const kind = mapLegacyKind(input.kind, undefined, name);
  const engine = mapLegacyEngine(input.kind, undefined, name);
  const fileId = typeof input.file_id === "string" ? input.file_id : "";

  return {
    id: fileId,
    projectId,
    folderId,
    name,
    ext,
    mime: mimeFromExt(ext),
    sizeBytes: typeof input.size === "number" ? Math.max(0, Math.round(input.size)) : 0,
    kind,
    engine,
    storageKey: `project/${projectId}/${folderId}/${name}`,
    createdAt: typeof input.created_at === "string" ? input.created_at : new Date().toISOString(),
    previewUrl:
      typeof input.thumb_url === "string"
        ? input.thumb_url
        : Array.isArray(input.preview_urls) && typeof input.preview_urls[0] === "string"
        ? String(input.preview_urls[0])
        : null,
    downloadUrl: fileId ? `/api/file/${encodeURIComponent(fileId)}?download=1` : null,
  };
}

async function loadExplorerList(req: Request, projectId: string, folderKey?: string) {
  const query = new URLSearchParams();
  query.set("project_id", projectId);
  if (folderKey) query.set("folder_key", folderKey);
  const upstream = await fetch(`${apiBase()}/explorer/list?${query.toString()}`, {
    headers: upstreamHeaders(req),
    cache: "no-store",
  });
  const payload = await readPayload(upstream);
  if (!upstream.ok) {
    throw new Error(readErrorMessage(payload, "Proje dosyaları alınamadı."));
  }
  if (!payload || typeof payload !== "object" || !Array.isArray((payload as { items?: unknown }).items)) {
    return [];
  }
  return ((payload as { items: unknown[] }).items || []).filter(
    (item): item is Record<string, unknown> => !!item && typeof item === "object"
  );
}

export async function GET(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const authHeaders = upstreamHeaders(req);
  let projectName = id === "default" ? "Default Project" : id;

  const projectRes = await fetch(`${apiBase()}/projects/${encodeURIComponent(id)}`, {
    headers: authHeaders,
    cache: "no-store",
  });
  const projectPayload = await readPayload(projectRes);
  if (projectRes.ok && projectPayload && typeof projectPayload === "object") {
    const rawName = (projectPayload as { name?: unknown }).name;
    if (typeof rawName === "string" && rawName.trim()) {
      projectName = rawName;
    }
  }

  const treeRes = await fetch(`${apiBase()}/explorer/tree?project_id=${encodeURIComponent(id)}`, {
    headers: authHeaders,
    cache: "no-store",
  });
  const treePayload = await readPayload(treeRes);
  if (!treeRes.ok) {
    return NextResponse.json(
      { error: readErrorMessage(treePayload, "Proje bulunamadı.") },
      { status: treeRes.status }
    );
  }

  const upstreamFolders =
    treePayload && typeof treePayload === "object" && Array.isArray((treePayload as { folders?: unknown }).folders)
      ? ((treePayload as { folders: unknown[] }).folders || []).filter(
          (item): item is Record<string, unknown> => !!item && typeof item === "object"
        )
      : [];

  const folders = upstreamFolders
    .map((folder) => {
      const folderKey = typeof folder.folder_key === "string" ? folder.folder_key : "";
      const label = typeof folder.label === "string" && folder.label.trim() ? folder.label : folderKey;
      if (!folderKey) return null;
      return {
        id: folderKey,
        projectId: id,
        name: label,
        parentId: typeof folder.parent_key === "string" && folder.parent_key.trim() ? folder.parent_key : null,
        isSystem: true,
        systemKey: folderKey,
        createdAt: new Date().toISOString(),
      };
    })
    .filter((item): item is NonNullable<typeof item> => !!item);

  const files = [];
  const seen = new Set<string>();

  try {
    if (folders.length > 0) {
      for (const folder of folders) {
        const items = await loadExplorerList(req, id, folder.id);
        for (const item of items) {
          const mapped = mapFileRecord(item, id, folder.id);
          if (!mapped.id || seen.has(mapped.id)) continue;
          seen.add(mapped.id);
          files.push(mapped);
        }
      }
    } else {
      const items = await loadExplorerList(req, id);
      for (const item of items) {
        const mapped = mapFileRecord(item, id, "root");
        if (!mapped.id || seen.has(mapped.id)) continue;
        seen.add(mapped.id);
        files.push(mapped);
      }
    }
  } catch (error) {
    return NextResponse.json(
      {
        error: error instanceof Error ? error.message : "Proje dosyaları alınamadı.",
      },
      { status: 502 }
    );
  }

  return NextResponse.json({
    projectId: id,
    projectName,
    folders,
    files,
  });
}

export async function POST(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const body = (await req.json().catch(() => ({}))) as Record<string, unknown>;
  const action = String(body.action || "");
  if (action === "deleteFiles") {
    const fileIds = Array.isArray(body.fileIds) ? body.fileIds.filter((v): v is string => typeof v === "string") : [];
    if (fileIds.length === 0) return NextResponse.json({ deleted: 0 });

    let deleted = 0;
    const authHeaders = upstreamHeaders(req, { "Content-Type": "application/json" });
    for (const fileId of fileIds) {
      const upstream = await fetch(`${apiBase()}/files/${encodeURIComponent(fileId)}/visibility`, {
        method: "PATCH",
        headers: authHeaders,
        body: JSON.stringify({ visibility: "hidden" }),
        cache: "no-store",
      });
      if (upstream.ok) {
        deleted += 1;
      }
    }
    return NextResponse.json({ deleted });
  }

  if (action === "createFolder" || action === "moveFiles") {
    return NextResponse.json(
      {
        error: "Bu backend sürümünde klasör oluşturma/taşıma desteklenmiyor.",
        action,
        projectId: id,
      },
      { status: 501 }
    );
  }

  return NextResponse.json({ error: "Geçersiz işlem." }, { status: 400 });
}
