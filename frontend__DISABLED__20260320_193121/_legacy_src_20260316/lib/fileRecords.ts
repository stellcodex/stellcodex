import { downloadFileText, getProject, uploadDirect } from "@/services/api";

export type PersistedRecord<T = Record<string, unknown>> = {
  record_id: string;
  kind: string;
  title: string;
  payload: T;
  deleted?: boolean;
  saved_at: string;
};

function nowIso() {
  return new Date().toISOString();
}

function createId(prefix: string) {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

export async function saveRecordFile<T extends Record<string, unknown>>(params: {
  projectId: string;
  kind: string;
  title: string;
  payload: T;
  recordId?: string;
  deleted?: boolean;
}) {
  const record: PersistedRecord<T> = {
    record_id: params.recordId || createId(params.kind),
    kind: params.kind,
    title: params.title,
    payload: params.payload,
    deleted: params.deleted || false,
    saved_at: nowIso(),
  };
  const filename = `${params.kind}__${record.record_id}__${Date.now()}.json`;
  const file = new File([JSON.stringify(record, null, 2)], filename, { type: "application/json" });
  const result = await uploadDirect(file, params.projectId);
  return { fileId: result.file_id, record };
}

export async function loadLatestRecords<T extends Record<string, unknown>>(projectId: string, kind: string) {
  const project = await getProject(projectId);
  const candidates = (project.files || [])
    .filter((file) => file.original_filename.endsWith(".json"))
    .sort((a, b) => (b.created_at || "").localeCompare(a.created_at || ""));

  const latestByRecord = new Map<string, PersistedRecord<T>>();
  for (const file of candidates) {
    if (!file.file_id) continue;
    try {
      const raw = await downloadFileText(file.file_id);
      const parsed = JSON.parse(raw) as PersistedRecord<T>;
      if (!parsed || parsed.kind !== kind || typeof parsed.record_id !== "string") continue;
      if (!latestByRecord.has(parsed.record_id)) {
        latestByRecord.set(parsed.record_id, parsed);
      }
    } catch {
      continue;
    }
  }
  return Array.from(latestByRecord.values()).filter((item) => !item.deleted);
}
