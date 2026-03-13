"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useUser } from "@/context/UserContext";
import { getSidebarPlatformApps, platformCategories } from "@/data/platformCatalog";
import {
  ensureSession,
  loadSessions,
  newSession,
  saveActiveSessionId,
  saveSessions,
  type WorkspaceSession,
} from "@/lib/sessionStore";
import { buildWorkspacePath, extractWorkspaceId, resolveWorkspaceHref } from "@/lib/workspace-routing";

type PlatformLayoutProps = {
  title: string;
  subtitle: string;
  children: React.ReactNode;
};

const NAV_ITEMS = [
  { href: "/", label: "Home" },
  { href: "/apps", label: "Applications" },
  { href: "/projects", label: "Projects" },
  { href: "/files", label: "Files" },
  { href: "/library", label: "Library" },
  { href: "/settings", label: "Settings" },
] as const;

function initials(name: string) {
  return (name || "SC")
    .split(" ")
    .map((part) => part[0] || "")
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

export function PlatformLayout({ title, subtitle, children }: PlatformLayoutProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useUser();
  const [collapsed, setCollapsed] = useState(false);
  const [sessions, setSessions] = useState<WorkspaceSession[]>([]);
  const [menuOpen, setMenuOpen] = useState(false);
  const workspaceId = extractWorkspaceId(pathname) || null;
  const settingsHref = resolveWorkspaceHref(workspaceId, "/settings");

  useEffect(() => {
    const session = ensureSession(workspaceId || undefined);
    setSessions(loadSessions().length > 0 ? loadSessions() : [session]);
    setMenuOpen(false);
  }, [workspaceId]);

  function handleNewWorkspace() {
    const created = newSession("Workspace");
    const next = [created, ...loadSessions()];
    saveSessions(next);
    saveActiveSessionId(created.id);
    setSessions(next);
    router.push(buildWorkspacePath(created.id));
  }

  function handleSelectWorkspace(sessionId: string) {
    saveActiveSessionId(sessionId);
    router.push(buildWorkspacePath(sessionId));
  }

  function isActive(target: string) {
    const href = resolveWorkspaceHref(workspaceId, target);
    if (href === pathname) return true;
    return href !== "/" && pathname.startsWith(`${href}/`);
  }

  const activeApps = getSidebarPlatformApps(user.role);

  return (
    <div className="layout-shell" data-collapsed={collapsed}>
      <aside className="layout-sidebar">
        <div className="page-section">
          <div className="brand-mark">STELLCODEX</div>
          <button className="button button--primary" type="button" onClick={handleNewWorkspace}>
            New workspace
          </button>
          <button className="button button--ghost" type="button" onClick={() => setCollapsed((value) => !value)}>
            {collapsed ? "Expand rail" : "Focus rail"}
          </button>
        </div>

        <section className="sidebar-section">
          <div className="sidebar-title">Navigation</div>
          <div className="sidebar-list">
            {NAV_ITEMS.map((item) => {
              const href = item.href === "/settings" ? settingsHref : resolveWorkspaceHref(workspaceId, item.href);
              return (
                <Link key={item.href} className="sidebar-link" data-active={isActive(item.href)} href={href}>
                  {collapsed ? item.label.slice(0, 1) : item.label}
                </Link>
              );
            })}
            {user.role === "admin" ? (
              <Link className="sidebar-link" data-active={isActive("/admin")} href={resolveWorkspaceHref(workspaceId, "/admin")}>
                {collapsed ? "A" : "Admin"}
              </Link>
            ) : null}
          </div>
        </section>

        <section className="sidebar-section">
          <div className="sidebar-title">Workspaces</div>
          <div className="sidebar-list">
            {sessions.slice(0, 8).map((session) => (
              <button
                key={session.id}
                className="session-button"
                data-active={session.id === workspaceId}
                type="button"
                onClick={() => handleSelectWorkspace(session.id)}
              >
                {collapsed ? session.title.slice(0, 1) : session.title}
              </button>
            ))}
          </div>
        </section>

        <section className="sidebar-section" style={{ overflowY: "auto" }}>
          <div className="sidebar-title">Applications</div>
          <div className="sidebar-list">
            {platformCategories.map((category) => {
              const items = activeApps.filter((app) => app.category === category);
              if (items.length === 0) return null;

              return (
                <div key={category}>
                  {!collapsed ? <div className="muted" style={{ marginBottom: "0.45rem", fontSize: "0.9rem" }}>{category}</div> : null}
                  <div className="sidebar-list">
                    {items.map((app) => (
                      <Link
                        key={app.id}
                        className="sidebar-link"
                        data-active={isActive(app.route)}
                        href={resolveWorkspaceHref(workspaceId, app.route)}
                      >
                        {collapsed ? app.shortName : app.name}
                      </Link>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      </aside>

      <div className="layout-main">
        <header className="layout-header">
          <div>
            <h1 className="page-title">{title}</h1>
            <p className="page-copy" style={{ margin: "0.35rem 0 0" }}>
              {subtitle}
            </p>
          </div>

          <div style={{ position: "relative" }}>
            <button className="button button--ghost" type="button" onClick={() => setMenuOpen((value) => !value)}>
              <span className="pill">{initials(user.name)}</span>
              <span>{user.name}</span>
            </button>

            {menuOpen ? (
              <div className="menu">
                <Link href={settingsHref}>Plan access</Link>
                <Link href={resolveWorkspaceHref(workspaceId, "/")}>Suite home</Link>
                <button
                  type="button"
                  onClick={() => {
                    logout();
                    setMenuOpen(false);
                    router.push("/");
                  }}
                >
                  Logout
                </button>
              </div>
            ) : null}
          </div>
        </header>

        <main className="layout-content">{children}</main>
      </div>
    </div>
  );
}
