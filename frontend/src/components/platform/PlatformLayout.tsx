"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { getSidebarPlatformApps, platformCategories } from "@/data/platformCatalog";
import { WorkspaceSession, ensureSession, loadSessions, newSession, saveActiveSessionId, saveSessions } from "@/lib/sessionStore";
import { buildWorkspacePath, extractWorkspaceId, resolveWorkspaceHref } from "@/lib/workspace-routing";
import { useUser } from "@/context/UserContext";

type PlatformLayoutProps = {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  mode?: "hub" | "workspace" | "focus";
  sessionState?: {
    sessions: WorkspaceSession[];
    activeSessionId: string | null;
    onSelectSession: (sessionId: string) => void;
    onNewSession: () => void;
  };
};

const baseNavItems = [
  { href: "/", label: "Home" },
  { href: "/files", label: "Files & Share" },
  { href: "/projects", label: "Projects" },
  { href: "/apps", label: "Applications" },
];

function initials(name: string) {
  return (name || "SC")
    .split(" ")
    .map((part) => part[0] || "")
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

export function PlatformLayout({ title, subtitle, children, mode = "workspace", sessionState }: PlatformLayoutProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout, isAuthenticated } = useUser();
  const [collapsed, setCollapsed] = useState(false);
  const [showMenu, setShowMenu] = useState(false);
  const [fallbackSessions, setFallbackSessions] = useState<WorkspaceSession[]>([]);
  const workspaceId = extractWorkspaceId(pathname);

  useEffect(() => {
    ensureSession(workspaceId || undefined);
    setFallbackSessions(loadSessions());
    setShowMenu(false);
  }, [pathname, workspaceId]);

  const sessions = sessionState?.sessions || fallbackSessions;
  const activeSessionId = sessionState?.activeSessionId || workspaceId || sessions[0]?.id || null;
  const apps = getSidebarPlatformApps(user.role).filter((app) => !["applications", "drive", "projects"].includes(app.id));
  const navItems = user.role === "admin" ? [...baseNavItems, { href: "/admin", label: "Admin" }] : baseNavItems;
  const modeLabel = mode === "focus" ? "Focused app" : mode === "hub" ? "Home" : "Workspace";

  function isActiveRoute(target: string, exactOnly = false) {
    if (pathname === target) return true;
    if (target.endsWith("/apps") && pathname.startsWith(target.replace(/\/apps$/, "/app/"))) return true;
    if (exactOnly) return false;
    return pathname.startsWith(`${target}/`);
  }

  function onCreateSession() {
    if (sessionState) {
      sessionState.onNewSession();
      return;
    }
    const created = newSession();
    const next = [created, ...loadSessions()];
    saveSessions(next);
    saveActiveSessionId(created.id);
    setFallbackSessions(next);
    router.push(buildWorkspacePath(created.id));
  }

  function onSelectSession(sessionId: string) {
    if (sessionState) {
      sessionState.onSelectSession(sessionId);
      return;
    }
    saveActiveSessionId(sessionId);
    router.push(buildWorkspacePath(sessionId));
  }

  return (
    <div className="flex min-h-screen bg-[var(--platform-bg)] text-[var(--platform-text)]">
      <aside
        className={`sticky top-0 hidden h-screen flex-col border-r border-[var(--border)] bg-[var(--platform-sidebar)] transition-all duration-200 lg:flex ${
          collapsed ? "w-[84px]" : "w-[272px]"
        }`}
      >
        <div className="flex h-16 items-center justify-between px-4">
          {!collapsed ? (
            <div>
              <div className="text-[11px] font-semibold uppercase tracking-[0.28em] text-[#111827]">STELLCODEX</div>
              <div className="mt-1 text-xs text-[#6b7280]">Files, projects, and apps</div>
            </div>
          ) : (
            <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#111827]">SC</div>
          )}
          <button
            type="button"
            onClick={() => setCollapsed((value) => !value)}
            className="rounded-lg border border-[var(--border)] bg-white px-2.5 py-1.5 text-xs text-[#4b5563] hover:bg-[#f8fafc]"
          >
            {collapsed ? "Open" : "Close"}
          </button>
        </div>

        <div className="px-4 pb-4">
          <button
            type="button"
            onClick={onCreateSession}
            className="flex w-full items-center justify-center rounded-2xl bg-[var(--accent)] px-3 py-3 text-sm font-medium text-white hover:opacity-95"
          >
            {collapsed ? "+" : "New workspace"}
          </button>
        </div>

        <nav className="space-y-1 px-3">
          {navItems.map((item) => {
            const href = resolveWorkspaceHref(workspaceId, item.href);
            const active = isActiveRoute(href, item.href === "/");
            return (
              <Link
                key={item.href}
                href={href}
                className={`flex items-center rounded-xl px-3 py-2 text-sm ${
                  active ? "bg-[var(--accent-soft)] text-[#111827]" : "text-[#4b5563] hover:bg-[#f8fafc] hover:text-[#111827]"
                }`}
              >
                {collapsed ? item.label.slice(0, 1) : item.label}
              </Link>
            );
          })}
        </nav>

        <div className="mt-5 px-4">
          <div className="mb-2 text-[11px] uppercase tracking-[0.2em] text-[#6b7280]">
            {collapsed ? "R" : "Recent"}
          </div>
          <div className="space-y-1">
            {sessions.slice(0, collapsed ? 6 : 10).map((session) => {
              const active = session.id === activeSessionId;
              return (
                <button
                  key={session.id}
                  type="button"
                  onClick={() => onSelectSession(session.id)}
                    className={`w-full rounded-xl px-3 py-2 text-left text-sm ${
                    active ? "bg-[var(--accent-soft)] text-[#111827]" : "text-[#4b5563] hover:bg-[#f8fafc] hover:text-[#111827]"
                  }`}
                >
                  {collapsed ? session.title.slice(0, 1) : session.title}
                </button>
              );
            })}
          </div>
        </div>

        {mode !== "hub" ? (
          <div className="mt-5 flex-1 overflow-y-auto px-4 pb-6">
            <div className="mb-2 text-[11px] uppercase tracking-[0.2em] text-[#6b7280]">
              {collapsed ? "A" : "Core apps"}
            </div>
            <div className="space-y-3">
              {platformCategories.map((category) => {
                const items = apps.filter((app) => app.category === category);
                if (items.length === 0) return null;
                return (
                  <div key={category}>
                    {!collapsed ? <div className="mb-1 text-xs text-[#6b7280]">{category}</div> : null}
                    <div className="space-y-1">
                      {items.map((app) => {
                        const href = resolveWorkspaceHref(workspaceId, app.route);
                        return (
                          <Link
                            key={app.id}
                            href={href}
                            className={`flex rounded-xl px-3 py-2 text-sm ${
                              pathname === href ? "bg-[var(--accent-soft)] text-[#111827]" : "text-[#4b5563] hover:bg-[#f8fafc] hover:text-[#111827]"
                            }`}
                          >
                            {collapsed ? app.shortName : app.name}
                          </Link>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ) : null}
      </aside>

      <div className="flex min-h-screen flex-1 flex-col">
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-[var(--border)] bg-white/96 px-4 backdrop-blur lg:px-6">
          <div className="min-w-0">
            <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[#6b7280]">{modeLabel}</div>
            <div className="truncate text-base font-semibold text-[#111827]">{title}</div>
            {subtitle ? <div className="truncate text-xs text-[#6b7280]">{subtitle}</div> : null}
          </div>

          <div className="relative flex items-center gap-2">
            {mode === "workspace" ? (
              <Link
                href={resolveWorkspaceHref(workspaceId, "/files")}
                className="hidden rounded-full border border-[var(--border)] px-3 py-2 text-sm text-[#374151] hover:bg-[#f8fafc] sm:inline-flex"
              >
                Upload
              </Link>
            ) : null}
            <button
              type="button"
              onClick={() => setShowMenu((value) => !value)}
              className="flex items-center gap-3 rounded-full border border-[var(--border)] bg-white px-2 py-1.5 text-sm text-[#111827] hover:bg-[#f8fafc]"
            >
              <span className="grid h-8 w-8 place-items-center rounded-full bg-[#e8f3f1] text-xs font-semibold text-[#0f766e]">
                {initials(user.name)}
              </span>
              <span className="hidden sm:block">{user.name}</span>
            </button>

            {showMenu ? (
              <div className="absolute right-0 mt-2 w-56 rounded-2xl border border-[var(--border)] bg-white p-2 shadow-[0_20px_50px_rgba(15,23,42,0.12)]">
                <div className="rounded-xl px-3 py-2 text-sm text-[#111827]">
                  <div>{user.name}</div>
                  <div className="text-xs text-[#6b7280]">{isAuthenticated ? "Signed in" : "Guest workspace"}</div>
                </div>
                <Link href={resolveWorkspaceHref(workspaceId, "/apps")} className="block rounded-xl px-3 py-2 text-sm text-[#374151] hover:bg-[#f8fafc]">
                  Applications
                </Link>
                <Link href={resolveWorkspaceHref(workspaceId, "/files")} className="block rounded-xl px-3 py-2 text-sm text-[#374151] hover:bg-[#f8fafc]">
                  Files & Share
                </Link>
                {user.role === "admin" ? (
                  <Link href={resolveWorkspaceHref(workspaceId, "/admin")} className="block rounded-xl px-3 py-2 text-sm text-[#374151] hover:bg-[#f8fafc]">
                    Admin
                  </Link>
                ) : null}
                <button
                  type="button"
                  onClick={() => {
                    setShowMenu(false);
                    logout();
                    router.push(resolveWorkspaceHref(workspaceId, "/"));
                  }}
                  className="mt-1 block w-full rounded-xl px-3 py-2 text-left text-sm text-[#b42318] hover:bg-[#fff5f5]"
                >
                  Logout
                </button>
              </div>
            ) : null}
          </div>
        </header>

        <main className={`flex-1 overflow-y-auto ${mode === "focus" ? "bg-[#fcfcfb]" : "bg-[var(--platform-bg)]"}`}>{children}</main>
      </div>
    </div>
  );
}
