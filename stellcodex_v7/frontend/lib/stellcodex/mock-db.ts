import { nanoid } from "nanoid";
import type {
  ArchiveEntry,
  FileDetailResponse,
  FileKind,
  FileRecord,
  FolderRecord,
  JobRecord,
  JobStage,
  JobStatus,
  ProjectRecord,
  ProjectTreeResponse,
  ShareLinkRecord,
  ViewerEngine,
} from "@/lib/stellcodex/types";

type MockDb = {
  projects: ProjectRecord[];
  folders: FolderRecord[];
  files: FileRecord[];
  jobs: JobRecord[];
  shares: ShareLinkRecord[];
};

const PROJECT_DEFAULT_NAME = "Genel";
const SYSTEM_FOLDERS = [
  { name: "3D Modeller", systemKey: "MODELS_3D" },
  { name: "2D Çizimler", systemKey: "DRAWINGS_2D" },
  { name: "Dokümanlar", systemKey: "DOCUMENTS" },
  { name: "Görseller", systemKey: "IMAGES" },
  { name: "Arşiv", systemKey: "ARCHIVE" },
] as const;

declare global {
  // eslint-disable-next-line no-var
  var __stellcodexMockDb: MockDb | undefined;
}

function nowIso() {
  return new Date().toISOString();
}

function extOf(name: string) {
  const parts = name.toLowerCase().split(".");
  return parts.length > 1 ? parts.pop() || "" : "";
}

function kindAndEngineByExt(ext: string): { kind: FileKind; engine: ViewerEngine; mime: string } {
  const e = ext.toLowerCase();
  if (["step", "stp", "iges", "igs", "stl", "obj", "sldprt"].includes(e)) {
    return { kind: "3d", engine: "viewer3d", mime: "model/octet-stream" };
  }
  if (e === "dxf") return { kind: "2d", engine: "viewer2d", mime: "image/vnd.dxf" };
  if (e === "pdf") return { kind: "pdf", engine: "pdf", mime: "application/pdf" };
  if (["jpg", "jpeg", "png", "webp"].includes(e)) return { kind: "image", engine: "image", mime: `image/${e === "jpg" ? "jpeg" : e}` };
  if (["docx", "xlsx", "pptx"].includes(e)) {
    return { kind: "office", engine: "office", mime: "application/octet-stream" };
  }
  if (e === "zip") return { kind: "zip", engine: "archive", mime: "application/zip" };
  return { kind: "unknown", engine: "unsupported", mime: "application/octet-stream" };
}

function stageByElapsed(ms: number): { stage: JobStage; status: JobStatus; progress: number } {
  if (ms < 900) return { stage: "uploaded", status: "RUNNING", progress: 15 };
  if (ms < 2200) return { stage: "security", status: "RUNNING", progress: 42 };
  if (ms < 3800) return { stage: "preview", status: "RUNNING", progress: 78 };
  return { stage: "ready", status: "SUCCEEDED", progress: 100 };
}

function getSystemFolderId(db: MockDb, projectId: string, systemKey: string) {
  const folder = db.folders.find((f) => f.projectId === projectId && f.systemKey === systemKey);
  if (!folder) throw new Error(`System folder missing: ${systemKey}`);
  return folder.id;
}

function folderSystemKeyForKind(kind: FileKind) {
  if (kind === "3d") return "MODELS_3D";
  if (kind === "2d") return "DRAWINGS_2D";
  if (kind === "pdf" || kind === "office") return "DOCUMENTS";
  if (kind === "image") return "IMAGES";
  if (kind === "zip") return "ARCHIVE";
  return "DOCUMENTS";
}

function makeFile(
  projectId: string,
  folderId: string,
  name: string,
  sizeBytes: number,
  extras?: Partial<FileRecord>
): FileRecord {
  const ext = extOf(name);
  const mapped = kindAndEngineByExt(ext);
  return {
    id: nanoid(12),
    projectId,
    folderId,
    name,
    ext,
    mime: mapped.mime,
    sizeBytes,
    kind: mapped.kind,
    engine: mapped.engine,
    storageKey: `mock/${projectId}/${folderId}/${name}`,
    createdAt: nowIso(),
    previewUrl: null,
    downloadUrl: null,
    archiveEntries: mapped.kind === "zip" ? [] : null,
    extractedFolderId: null,
    ...extras,
  };
}

function makeJob(fileId: string, overrides?: Partial<JobRecord>): JobRecord {
  const ts = nowIso();
  return {
    id: nanoid(12),
    fileId,
    status: "RUNNING",
    stage: "uploaded",
    progress: 10,
    error: null,
    createdAt: ts,
    updatedAt: ts,
    startedAtMs: Date.now(),
    riskFlags: [],
    ...overrides,
  };
}

function seedDb(): MockDb {
  const projectId = nanoid(10);
  const project: ProjectRecord = { id: projectId, name: PROJECT_DEFAULT_NAME, ownerId: null, createdAt: nowIso() };

  const folders: FolderRecord[] = SYSTEM_FOLDERS.map((f) => ({
    id: nanoid(10),
    projectId,
    name: f.name,
    parentId: null,
    isSystem: true,
    systemKey: f.systemKey,
    createdAt: nowIso(),
  }));

  const byKey = (key: string) => folders.find((f) => f.systemKey === key)!;
  const files: FileRecord[] = [
    makeFile(projectId, byKey("MODELS_3D").id, "ornek-parca.step", 2_400_000),
    makeFile(projectId, byKey("MODELS_3D").id, "kutu.stl", 680_000),
    makeFile(projectId, byKey("DRAWINGS_2D").id, "yerlesim.dxf", 214_000),
    makeFile(projectId, byKey("DOCUMENTS").id, "teklif.pdf", 540_000),
    makeFile(projectId, byKey("DOCUMENTS").id, "kontrol-listesi.docx", 120_000),
    makeFile(projectId, byKey("IMAGES").id, "urun.png", 800_000),
    makeFile(projectId, byKey("ARCHIVE").id, "paket.zip", 4_100_000, {
      archiveEntries: [
        { path: "docs/readme.pdf", sizeBytes: 54_000, kind: "pdf" },
        { path: "models/bracket.step", sizeBytes: 900_000, kind: "3d" },
        { path: "drawings/sheet.dxf", sizeBytes: 180_000, kind: "2d" },
      ],
    }),
  ];

  const jobs: JobRecord[] = files.map((file, idx) => {
    if (idx === 0) return makeJob(file.id, { stage: "ready", status: "SUCCEEDED", progress: 100, startedAtMs: Date.now() - 20_000 });
    if (idx === 1) return makeJob(file.id, { stage: "preview", status: "RUNNING", progress: 70, startedAtMs: Date.now() - 2500 });
    if (idx === 2) return makeJob(file.id, { stage: "security", status: "RUNNING", progress: 35, startedAtMs: Date.now() - 1200 });
    if (idx === 3) return makeJob(file.id, { stage: "ready", status: "NEEDS_APPROVAL", progress: 100, riskFlags: ["RISK_MANUFACTURING"], startedAtMs: Date.now() - 20_000 });
    return makeJob(file.id, { stage: "ready", status: "SUCCEEDED", progress: 100, startedAtMs: Date.now() - 20_000 });
  });

  const shares: ShareLinkRecord[] = [
    {
      id: nanoid(10),
      fileId: files[0].id,
      token: "demo-share-token",
      canView: true,
      canDownload: true,
      passwordHash: null,
      expiresAt: null,
      createdAt: nowIso(),
    },
  ];

  return { projects: [project], folders, files, jobs, shares };
}

function getDb(): MockDb {
  if (!globalThis.__stellcodexMockDb) globalThis.__stellcodexMockDb = seedDb();
  return globalThis.__stellcodexMockDb;
}

function touchJob(job: JobRecord) {
  if (job.status === "FAILED" || job.status === "NEEDS_APPROVAL") return job;
  const elapsed = Date.now() - (job.startedAtMs || Date.now());
  const next = stageByElapsed(elapsed);
  job.stage = next.stage;
  job.status = next.status;
  job.progress = next.progress;
  job.updatedAt = nowIso();
  return job;
}

export function listJobs() {
  return getDb()
    .jobs.map((j) => touchJob(j))
    .sort((a, b) => (a.updatedAt < b.updatedAt ? 1 : -1));
}

export function getJob(jobId: string) {
  const job = getDb().jobs.find((j) => j.id === jobId);
  if (!job) return null;
  return touchJob(job);
}

export function getJobByFileId(fileId: string) {
  const job = getDb().jobs.find((j) => j.fileId === fileId);
  if (!job) return null;
  return touchJob(job);
}

export function getDefaultProject() {
  const db = getDb();
  return db.projects[0];
}

export function getProjectTree(projectId: string): ProjectTreeResponse | null {
  const db = getDb();
  const project = db.projects.find((p) => p.id === projectId);
  if (!project) return null;
  return {
    projectId: project.id,
    projectName: project.name,
    folders: db.folders.filter((f) => f.projectId === project.id),
    files: db.files.filter((f) => f.projectId === project.id),
  };
}

function filePreviewPlaceholder(file: FileRecord) {
  if (file.kind === "image") return "/favicon-32x32.png";
  if (file.kind === "pdf") return "/apple-touch-icon.png";
  return null;
}

export function getFileDetail(fileId: string): FileDetailResponse | null {
  const db = getDb();
  const file = db.files.find((f) => f.id === fileId);
  if (!file) return null;
  return {
    file,
    previewUrl: file.previewUrl ?? filePreviewPlaceholder(file),
    downloadUrl: `/api/file/${file.id}?download=1`,
    inFolder: db.folders.find((f) => f.id === file.folderId) || null,
    job: getJobByFileId(file.id),
  };
}

export function resolveViewer(fileId: string) {
  const file = getDb().files.find((f) => f.id === fileId);
  if (!file) return null;
  return { engine: file.engine, kind: file.kind };
}

export function createFolder(input: { projectId: string; parentId?: string | null; name: string }) {
  const db = getDb();
  const folder: FolderRecord = {
    id: nanoid(10),
    projectId: input.projectId,
    parentId: input.parentId ?? null,
    name: input.name.trim() || "Yeni Klasör",
    isSystem: false,
    systemKey: null,
    createdAt: nowIso(),
  };
  db.folders.push(folder);
  return folder;
}

export function moveFiles(input: { fileIds: string[]; folderId: string }) {
  const db = getDb();
  const updated: FileRecord[] = [];
  for (const file of db.files) {
    if (input.fileIds.includes(file.id)) {
      file.folderId = input.folderId;
      updated.push(file);
    }
  }
  return updated;
}

export function deleteFiles(fileIds: string[]) {
  const db = getDb();
  const deletableIds = new Set(fileIds);
  db.files = db.files.filter((f) => !deletableIds.has(f.id));
  db.jobs = db.jobs.filter((j) => !deletableIds.has(j.fileId));
  db.shares = db.shares.filter((s) => !deletableIds.has(s.fileId));
  return { deleted: fileIds.length };
}

export function createUpload(input: { projectId?: string | null; fileName: string; sizeBytes: number; mime?: string | null }) {
  const db = getDb();
  const project = input.projectId ? db.projects.find((p) => p.id === input.projectId) || db.projects[0] : db.projects[0];
  const ext = extOf(input.fileName);
  const mapped = kindAndEngineByExt(ext);
  const folderId = getSystemFolderId(db, project.id, folderSystemKeyForKind(mapped.kind));
  const file = makeFile(project.id, folderId, input.fileName, input.sizeBytes, {
    mime: input.mime || mapped.mime,
    kind: mapped.kind,
    engine: mapped.engine,
    archiveEntries:
      mapped.kind === "zip"
        ? [
            { path: "nested/a.step", sizeBytes: 420_000, kind: "3d" },
            { path: "nested/b.pdf", sizeBytes: 88_000, kind: "pdf" },
          ]
        : null,
  });
  db.files.unshift(file);
  const job = makeJob(file.id, { status: "RUNNING", stage: "uploaded", progress: 8, startedAtMs: Date.now() });
  db.jobs.unshift(job);
  return { fileId: file.id, jobId: job.id };
}

export function createShare(input: {
  fileId: string;
  canView?: boolean;
  canDownload?: boolean;
  password?: string | null;
  expiresAt?: string | null;
}) {
  const db = getDb();
  const file = db.files.find((f) => f.id === input.fileId);
  if (!file) return null;
  const token = nanoid(16);
  const share: ShareLinkRecord = {
    id: nanoid(10),
    fileId: file.id,
    token,
    canView: input.canView ?? true,
    canDownload: input.canDownload ?? false,
    passwordHash: input.password ? "placeholder_hash" : null,
    expiresAt: input.expiresAt ?? null,
    createdAt: nowIso(),
  };
  db.shares.unshift(share);
  return { share, shareUrl: `/s/${token}` };
}

export function getShareByToken(token: string) {
  const db = getDb();
  const share = db.shares.find((s) => s.token === token);
  if (!share) return null;
  const fileDetail = getFileDetail(share.fileId);
  if (!fileDetail) return null;
  return { share, file: fileDetail.file, previewUrl: fileDetail.previewUrl, downloadUrl: fileDetail.downloadUrl };
}

export function listArchive(fileId: string): ArchiveEntry[] | null {
  const file = getDb().files.find((f) => f.id === fileId);
  if (!file || file.kind !== "zip") return null;
  return file.archiveEntries || [];
}

export function extractArchive(fileId: string) {
  const db = getDb();
  const zipFile = db.files.find((f) => f.id === fileId);
  if (!zipFile || zipFile.kind !== "zip") return null;
  if (zipFile.extractedFolderId) return { newFolderId: zipFile.extractedFolderId };

  const archiveFolder = db.folders.find((f) => f.id === zipFile.folderId);
  const newFolder: FolderRecord = {
    id: nanoid(10),
    projectId: zipFile.projectId,
    parentId: archiveFolder?.id || null,
    name: `${zipFile.name.replace(/\.zip$/i, "")}_extracted`,
    isSystem: false,
    systemKey: null,
    createdAt: nowIso(),
  };
  db.folders.push(newFolder);
  zipFile.extractedFolderId = newFolder.id;

  for (const entry of zipFile.archiveEntries || []) {
    const name = entry.path.split("/").pop() || entry.path;
    const f = makeFile(zipFile.projectId, newFolder.id, name, entry.sizeBytes);
    db.files.push(f);
    db.jobs.push(
      makeJob(f.id, {
        stage: "security",
        status: "RUNNING",
        progress: 28,
        startedAtMs: Date.now() - 900,
      })
    );
  }
  return { newFolderId: newFolder.id };
}

export function adminSnapshot() {
  const jobs = listJobs();
  const pendingApprovals = jobs.filter((j) => j.status === "NEEDS_APPROVAL");
  return {
    jobs,
    pendingApprovals,
    systemInfo: {
      projectCount: getDb().projects.length,
      fileCount: getDb().files.length,
      shareCount: getDb().shares.length,
      workerStatus: "mock-online",
      db: process.env.DATABASE_URL ? "configured" : "mock-only",
      neonConfigured: Boolean(process.env.DATABASE_URL),
    },
  };
}

