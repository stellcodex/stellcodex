"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { getVisiblePlatformApps, platformCategories } from "@/data/platformCatalog";
import {
  type WorkspaceSession,
  ensureSession,
  loadSessions,
  newSession,
  saveActiveSessionId,
  saveSessions,
} from "@/lib/sessionStore";
import { buildWorkspacePath, extractWorkspaceId, resolveWorkspaceHref } from "@/lib/workspace-routing";
import { useUser } from "@/context/UserContext";

type PlatformLayoutProps = {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  sessionState?: {
    sessions: WorkspaceSession[];
    activeSessionId: string | null;
    onSelectSession: (sessionId: string) => void;
    onNewSession: () => void;
  };
};

const baseNavItems = [
  { href: "/", label: "Workspace" },
  { href: "/projects", label: "Projects" },
  { href: "/files", label: "Files" },
  { href: "/library", label: "Library" },
  { href: "/settings", label: "Settings" },
];

function initials(name: string) {
  return (name || "SC")
    .split(" ")
    .map((part) => part[0] || "")
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

export function PlatformLayout({ title, subtitle, children, sessionState }: PlatformLayoutProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout, isAuthenticated } = useUser();
  const [collapsed, setCollapsed] = useState(false);
  const [showMenu, setShowMenu] = useState(false);
  const [showBeta, setShowBeta] = useState(false);
  const [fallbackSessions, setFallbackSessions] = useState<WorkspaceSession[]>([]);
  const workspaceId = extractWorkspaceId(pathname);

  useEffect(() => {
    ensureSession(workspaceId || undefined);
    setFallbackSessions(loadSessions());
    setShowMenu(false);
  }, [pathname, workspaceId]);

  const sessions = sessionState?.sessions || fallbackSessions;
  const activeSessionId = sessionState?.activeSessionId || workspaceId || sessions[0]?.id || null;
  const apps = getVisiblePlatformApps(user.role, { showBeta });
  const navItems = user.role === "admin" ? [...baseNavItems, { href: "/admin", label: "Admin" }] : baseNavItems;

  function isActiveRoute(target: string, exactOnly = false) {
    if (pathname === target) return true;
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
        className={`sticky top-0 hidden h-screen flex-col border-r border-[#e5e7eb] bg-white transition-all duration-200 lg:flex ${
          collapsed ? "w-[80px]" : "w-[280px]"
        }`}
      >
        <div className="flex h-16 items-center justify-between px-4">
          {!collapsed ? <div className="text-xs font-semibold tracking-[0.24em] text-[#111827]">STELLCODEX</div> : <div />}
          <button
            type="button"
            onClick={() => setCollapsed((value) => !value)}
            className="rounded-lg border border-[#d1d5db] bg-white px-2.5 py-1.5 text-xs text-[#374151] hover:bg-[#f9fafb]"
          >
            {collapsed ? ">>" : "<<"}
          </button>
        </div>

        <div className="px-4 pb-3">
          <button
            type="button"
            onClick={onCreateSession}
            className="flex w-full items-center justify-center rounded-xl border border-[#111827] bg-[#111827] px-3 py-2.5 text-sm font-medium text-white hover:bg-[#1f2937]"
          >
            {collapsed ? "+" : "New Session"}
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
                  active ? "bg-[#f3f4f6] text-[#111827]" : "text-[#374151] hover:bg-[#f9fafb] hover:text-[#111827]"
                }`}
              >
                {collapsed ? item.label.slice(0, 1) : item.label}
              </Link>
            );
          })}
        </nav>

        <div className="mt-5 px-4">
          <div className="mb-2 text-[11px] uppercase tracking-[0.2em] text-[#9ca3af]">{collapsed ? "S" : "Sessions"}</div>
          <div className="space-y-1">
            {sessions.slice(0, collapsed ? 6 : 10).map((session) => {
              const active = session.id === activeSessionId;
              return (
                <button
                  key={session.id}
                  type="button"
                  onClick={() => onSelectSession(session.id)}
                  className={`w-full rounded-xl px-3 py-2 text-left text-sm ${
                    active ? "bg-[#f3f4f6] text-[#111827]" : "text-[#4b5563] hover:bg-[#f9fafb] hover:text-[#111827]"
                  }`}
                >
                  {collapsed ? session.title.slice(0, 1) : session.title}
                </button>
              );
            })}
          </div>
        </div>

        <div className="mt-5 flex-1 overflow-y-auto px-4 pb-6">
          <div className="mb-2 flex items-center justify-between gap-2">
            <div className="text-[11px] uppercase tracking-[0.2em] text-[#9ca3af]">{collapsed ? "A" : "Applications"}</div>
            {!collapsed ? (
              <button
                type="button"
                onClick={() => setShowBeta((value) => !value)}
                className={`rounded-full border px-2 py-0.5 text-[10px] ${
                  showBeta
                    ? "border-[#111827] bg-[#111827] text-white"
                    : "border-[#d1d5db] bg-white text-[#4b5563] hover:bg-[#f9fafb]"
                }`}
              >
                Show beta
              </button>
            ) : null}
          </div>
          <div className="space-y-3">
            {platformCategories.map((category) => {
              const items = apps.filter((app) => app.category === category);
              if (items.length === 0) return null;
              return (
                <div key={category}>
                  {!collapsed ? <div className="mb-1 text-xs text-[#9ca3af]">{category}</div> : null}
                  <div className="space-y-1">
                    {items.map((app) => {
                      const href = resolveWorkspaceHref(workspaceId, app.route);
                      const active = pathname === href;
                      return (
                        <Link
                          key={app.id}
                          href={href}
                          className={`flex items-center justify-between rounded-xl px-3 py-2 text-sm ${
                            active ? "bg-[#f3f4f6] text-[#111827]" : "text-[#4b5563] hover:bg-[#f9fafb] hover:text-[#111827]"
                          }`}
                        >
                          <span>{collapsed ? app.shortName : app.name}</span>
                          {!collapsed && app.status === "beta" ? (
                            <span className="rounded-full border border-[#d1d5db] px-1.5 py-0.5 text-[10px] text-[#6b7280]">BETA</span>
                          ) : null}
                        </Link>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </aside>

      <div className="flex min-h-screen flex-1 flex-col">
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-[#e5e7eb] bg-white px-4">
          <div>
            <div className="text-sm font-semibold text-[#111827]">{title}</div>
            {subtitle ? <div className="text-xs text-[#6b7280]">{subtitle}</div> : null}
          </div>

          <div className="relative">
            <button
              type="button"
              onClick={() => setShowMenu((value) => !value)}
              className="flex items-center gap-3 rounded-full border border-[#d1d5db] bg-white px-2 py-1.5 text-sm text-[#111827] hover:bg-[#f9fafb]"
            >
              <span className="grid h-8 w-8 place-items-center rounded-full bg-[#eef2ff] text-xs font-semibold text-[#1e3a8a]">
                {initials(user.name)}
              </span>
              <span className="hidden sm:block">{user.name}</span>
            </button>

            {showMenu ? (
              <div className="absolute right-0 mt-2 w-56 rounded-2xl border border-[#e5e7eb] bg-white p-2 shadow-xl">
                <div className="rounded-xl px-3 py-2 text-sm text-[#111827]">
                  <div>{user.name}</div>
                  <div className="text-xs text-[#6b7280]">{isAuthenticated ? "Signed in" : "Guest workspace"}</div>
                </div>
                <Link href={resolveWorkspaceHref(workspaceId, "/settings")} className="block rounded-xl px-3 py-2 text-sm text-[#374151] hover:bg-[#f9fafb]">
                  Plan
                </Link>
                <Link href={resolveWorkspaceHref(workspaceId, "/settings")} className="block rounded-xl px-3 py-2 text-sm text-[#374151] hover:bg-[#f9fafb]">
                  Settings
                </Link>
                <Link href={resolveWorkspaceHref(workspaceId, "/")} className="block rounded-xl px-3 py-2 text-sm text-[#374151] hover:bg-[#f9fafb]">
                  Explore Applications
                </Link>
                <button
                  type="button"
                  onClick={() => {
                    setShowMenu(false);
                    logout();
                    router.push(resolveWorkspaceHref(workspaceId, "/"));
                  }}
                  className="mt-1 block w-full rounded-xl px-3 py-2 text-left text-sm text-[#b91c1c] hover:bg-[#fef2f2]"
                >
                  Logout
                </button>
              </div>
            ) : null}
          </div>
        </header>

        <main className="flex-1 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}
