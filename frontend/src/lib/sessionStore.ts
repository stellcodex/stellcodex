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
    text: "STELLCODEX workspace hazir. Explore Applications ile uygulama acabilir, dosya yukleyebilir veya proje akisini baslatabilirsiniz.",
    createdAt: nowIso(),
  };
}

export function newSession(title = "New session"): WorkspaceSession {
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
    session.title === "New session" && role === "user"
      ? text.trim().slice(0, 42) || session.title
      : session.title;
  return {
    ...session,
    title,
    updatedAt: nowIso(),
    messages: nextMessages,
  };
}
