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
  sessionState?: {
    sessions: WorkspaceSession[];
    activeSessionId: string | null;
    onSelectSession: (sessionId: string) => void;
    onNewSession: () => void;
  };
};

const baseNavItems = [
  { href: "/", label: "Workspace" },
  { href: "/apps", label: "Applications" },
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
  const [fallbackSessions, setFallbackSessions] = useState<WorkspaceSession[]>([]);
  const workspaceId = extractWorkspaceId(pathname);

  useEffect(() => {
    ensureSession(workspaceId || undefined);
    setFallbackSessions(loadSessions());
    setShowMenu(false);
  }, [pathname, workspaceId]);

  const sessions = sessionState?.sessions || fallbackSessions;
  const activeSessionId = sessionState?.activeSessionId || workspaceId || sessions[0]?.id || null;
  const apps = getSidebarPlatformApps(user.role);
  const navItems = user.role === "admin" ? [...baseNavItems, { href: "/admin", label: "Admin" }] : baseNavItems;

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
        className={`sticky top-0 hidden h-screen flex-col border-r border-white/10 bg-[var(--platform-sidebar)] transition-all duration-200 lg:flex ${
          collapsed ? "w-[76px]" : "w-[260px]"
        }`}
      >
        <div className="flex h-14 items-center justify-between px-3">
          {!collapsed ? <div className="text-xs font-semibold tracking-[0.28em] text-white/55">STELLCODEX</div> : <div />}
          <button
            type="button"
            onClick={() => setCollapsed((value) => !value)}
            className="rounded-lg border border-white/10 bg-white/5 px-2.5 py-1.5 text-xs text-white/70 hover:bg-white/10"
          >
            {collapsed ? ">>" : "<<"}
          </button>
        </div>

        <div className="px-3 pb-3">
          <button
            type="button"
            onClick={onCreateSession}
            className="flex w-full items-center justify-center rounded-2xl bg-white/7 px-3 py-3 text-sm font-medium text-white hover:bg-white/12"
          >
            {collapsed ? "+" : "New session"}
          </button>
        </div>

        <nav className="space-y-1 px-2">
          {navItems.map((item) => {
            const href = resolveWorkspaceHref(workspaceId, item.href);
            const active = isActiveRoute(href, item.href === "/");
            return (
              <Link
                key={item.href}
                href={href}
                className={`flex items-center rounded-xl px-3 py-2 text-sm ${
                  active ? "bg-white/12 text-white" : "text-white/65 hover:bg-white/6 hover:text-white"
                }`}
              >
                {collapsed ? item.label.slice(0, 1) : item.label}
              </Link>
            );
          })}
        </nav>

        <div className="mt-5 px-3">
          <div className="mb-2 text-[11px] uppercase tracking-[0.2em] text-white/35">
            {collapsed ? "S" : "Sessions"}
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
                    active ? "bg-white/12 text-white" : "text-white/58 hover:bg-white/6 hover:text-white"
                  }`}
                >
                  {collapsed ? session.title.slice(0, 1) : session.title}
                </button>
              );
            })}
          </div>
        </div>

        <div className="mt-5 flex-1 overflow-y-auto px-3 pb-6">
          <div className="mb-2 text-[11px] uppercase tracking-[0.2em] text-white/35">
            {collapsed ? "A" : "Applications"}
          </div>
          <div className="space-y-3">
            {platformCategories.map((category) => {
              const items = apps.filter((app) => app.category === category);
              if (items.length === 0) return null;
              return (
                <div key={category}>
                  {!collapsed ? <div className="mb-1 text-xs text-white/35">{category}</div> : null}
                  <div className="space-y-1">
                    {items.map((app) => {
                      const href = resolveWorkspaceHref(workspaceId, app.route);
                      return (
                        <Link
                          key={app.id}
                          href={href}
                          className={`flex rounded-xl px-3 py-2 text-sm ${
                            pathname === href ? "bg-white/12 text-white" : "text-white/58 hover:bg-white/6 hover:text-white"
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
      </aside>

      <div className="flex min-h-screen flex-1 flex-col">
        <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-white/10 bg-[var(--platform-bg)]/92 px-4 backdrop-blur">
          <div>
            <div className="text-sm font-semibold text-white">{title}</div>
            {subtitle ? <div className="text-xs text-white/40">{subtitle}</div> : null}
          </div>

          <div className="relative">
            <button
              type="button"
              onClick={() => setShowMenu((value) => !value)}
              className="flex items-center gap-3 rounded-full border border-white/10 bg-white/5 px-2 py-1.5 text-sm text-white/85 hover:bg-white/10"
            >
              <span className="grid h-8 w-8 place-items-center rounded-full bg-emerald-500/20 text-xs font-semibold text-emerald-200">
                {initials(user.name)}
              </span>
              <span className="hidden sm:block">{user.name}</span>
            </button>

            {showMenu ? (
              <div className="absolute right-0 mt-2 w-56 rounded-2xl border border-white/10 bg-[#171717] p-2 shadow-2xl">
                <div className="rounded-xl px-3 py-2 text-sm text-white/85">
                  <div>{user.name}</div>
                  <div className="text-xs text-white/45">{isAuthenticated ? "Signed in" : "Guest workspace"}</div>
                </div>
                <Link href={resolveWorkspaceHref(workspaceId, "/settings")} className="block rounded-xl px-3 py-2 text-sm text-white/80 hover:bg-white/8">
                  Plan
                </Link>
                <Link href={resolveWorkspaceHref(workspaceId, "/settings")} className="block rounded-xl px-3 py-2 text-sm text-white/80 hover:bg-white/8">
                  Settings
                </Link>
                <Link href={resolveWorkspaceHref(workspaceId, "/")} className="block rounded-xl px-3 py-2 text-sm text-white/80 hover:bg-white/8">
                  Explore Applications
                </Link>
                <button
                  type="button"
                  onClick={() => {
                    setShowMenu(false);
                    logout();
                    router.push(resolveWorkspaceHref(workspaceId, "/"));
                  }}
                  className="mt-1 block w-full rounded-xl px-3 py-2 text-left text-sm text-red-200 hover:bg-red-500/10"
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
