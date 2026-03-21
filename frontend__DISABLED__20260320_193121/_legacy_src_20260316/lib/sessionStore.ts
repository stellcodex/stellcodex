"use client";

export type WorkspaceMessage = {
  id: string;
  role: "user" | "assistant";
  text: string;
  createdAt: string;
};

export type WorkspaceSession = {
  id: string;
  title: string;
  updatedAt: string;
  messages: WorkspaceMessage[];
};

const STORE_KEY = "stellcodex_workspace_sessions_v1";
const ACTIVE_KEY = "stellcodex_workspace_active_session_v1";

function nowIso() {
  return new Date().toISOString();
}

function createId(prefix: string) {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

function defaultAssistantMessage(): WorkspaceMessage {
  return {
    id: createId("msg"),
    role: "assistant",
    text: "The STELLCODEX workspace is ready. You can upload files, open projects, and continue working immediately.",
    createdAt: nowIso(),
  };
}

export function newSession(title = "Workspace"): WorkspaceSession {
  return {
    id: createId("session"),
    title,
    updatedAt: nowIso(),
    messages: [defaultAssistantMessage()],
  };
}

export function loadSessions(): WorkspaceSession[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(STORE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((item) => item && typeof item.id === "string");
  } catch {
    return [];
  }
}

export function saveSessions(sessions: WorkspaceSession[]) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(STORE_KEY, JSON.stringify(sessions));
}

export function loadActiveSessionId() {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(ACTIVE_KEY);
}

export function saveActiveSessionId(sessionId: string) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(ACTIVE_KEY, sessionId);
}

export function getSessionById(sessionId: string | null | undefined, sessions = loadSessions()) {
  if (!sessionId) return null;
  return sessions.find((item) => item.id === sessionId) || null;
}

export function ensureSession(sessionId?: string | null, title = "Workspace"): WorkspaceSession {
  const sessions = loadSessions();

  if (sessionId) {
    const existing = getSessionById(sessionId, sessions);
    if (existing) {
      saveActiveSessionId(existing.id);
      return existing;
    }

    const created = {
      ...newSession(title),
      id: sessionId,
      title,
    };
    saveSessions([created, ...sessions]);
    saveActiveSessionId(created.id);
    return created;
  }

  const activeId = loadActiveSessionId();
  const active = getSessionById(activeId, sessions) || sessions[0] || null;
  if (active) {
    saveActiveSessionId(active.id);
    return active;
  }

  const created = newSession(title);
  saveSessions([created]);
  saveActiveSessionId(created.id);
  return created;
}

export function upsertSession(session: WorkspaceSession) {
  const sessions = loadSessions().filter((item) => item.id !== session.id);
  const next = [session, ...sessions].sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
  saveSessions(next);
  saveActiveSessionId(session.id);
  return next;
}

export function appendSessionMessage(
  session: WorkspaceSession,
  role: WorkspaceMessage["role"],
  text: string
): WorkspaceSession {
  const nextMessages = [
    ...session.messages,
    {
      id: createId("msg"),
      role,
      text,
      createdAt: nowIso(),
    },
  ];
  const title =
    (session.title === "New session" || session.title === "Workspace") && role === "user"
      ? text.trim().slice(0, 42) || session.title
      : session.title;
  return {
    ...session,
    title,
    updatedAt: nowIso(),
    messages: nextMessages,
  };
}
