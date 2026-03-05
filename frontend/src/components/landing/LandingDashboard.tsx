"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { getVisiblePlatformApps } from "@/data/platformCatalog";
import { loadSessions } from "@/lib/sessionStore";
import { useUser } from "@/context/UserContext";

function workspaceEntryHref(route: string) {
  if (route === "/workspace") return "/workspace";
  if (route.startsWith("/app/")) {
    return `/workspace?next=${encodeURIComponent(route)}`;
  }
  return route;
}

export function LandingDashboard() {
  const { user } = useUser();
  const [showBeta, setShowBeta] = useState(false);
  const apps = useMemo(
    () => getVisiblePlatformApps(user.role, { showBeta }).filter((app) => app.id !== "workspace"),
    [showBeta, user.role]
  );
  const sessions = useMemo(() => loadSessions().slice(0, 8), []);

  return (
    <div className="min-h-screen bg-white text-[#111827]">
      <div className="mx-auto grid max-w-[1320px] gap-6 px-4 py-6 lg:grid-cols-[280px_minmax(0,1fr)] lg:px-8">
        <aside className="rounded-2xl border border-[#e5e7eb] bg-white p-4">
          <div className="text-xs font-semibold tracking-[0.24em] text-[#111827]">STELLCODEX</div>
          <div className="mt-6 space-y-2">
            <Link
              href="/workspace"
              className="inline-flex h-11 w-full items-center justify-center rounded-xl border border-[#111827] bg-[#111827] px-4 text-sm font-medium text-white hover:bg-[#1f2937]"
            >
              New Workspace
            </Link>
            <Link
              href="/upload"
              className="inline-flex h-11 w-full items-center justify-center rounded-xl border border-[#d1d5db] bg-white px-4 text-sm font-medium text-[#111827] hover:bg-[#f9fafb]"
            >
              Upload File
            </Link>
          </div>

          {sessions.length > 0 ? (
            <div className="mt-8">
              <div className="mb-2 text-[11px] uppercase tracking-[0.2em] text-[#9ca3af]">Recent Sessions</div>
              <div className="space-y-1.5">
                {sessions.map((session) => (
                  <Link
                    key={session.id}
                    href={`/workspace/${encodeURIComponent(session.id)}`}
                    className="block rounded-xl border border-[#f3f4f6] px-3 py-2 text-sm text-[#374151] hover:border-[#e5e7eb] hover:bg-[#f9fafb]"
                  >
                    <div className="truncate font-medium text-[#111827]">{session.title || "Workspace"}</div>
                    <div className="truncate text-xs text-[#6b7280]">{session.id}</div>
                  </Link>
                ))}
              </div>
            </div>
          ) : null}
        </aside>

        <main className="space-y-6">
          <section className="rounded-2xl border border-[#e5e7eb] bg-white p-6">
            <h1 className="text-3xl font-semibold tracking-tight text-[#111827]">STELLCODEX Landing Dashboard</h1>
            <p className="mt-2 max-w-3xl text-sm text-[#4b5563]">
              Upload, process, view, analyze, run agents and share outputs from one workspace entry point.
            </p>
          </section>

          <section className="rounded-2xl border border-[#e5e7eb] bg-white p-6">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold text-[#111827]">Active Apps</h2>
                <p className="text-sm text-[#6b7280]">Only end-to-end connected applications are shown by default.</p>
              </div>
              <button
                type="button"
                onClick={() => setShowBeta((value) => !value)}
                className={`rounded-full border px-3 py-1 text-xs ${
                  showBeta
                    ? "border-[#111827] bg-[#111827] text-white"
                    : "border-[#d1d5db] bg-white text-[#4b5563] hover:bg-[#f9fafb]"
                }`}
              >
                Show beta
              </button>
            </div>

            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {apps.map((app) => (
                <Link
                  key={app.id}
                  href={workspaceEntryHref(app.route)}
                  className="rounded-xl border border-[#e5e7eb] bg-white p-4 transition hover:border-[#d1d5db] hover:bg-[#f9fafb]"
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className="text-sm font-semibold text-[#111827]">{app.name}</div>
                    <div className="rounded-full border border-[#d1d5db] px-2 py-0.5 text-[10px] font-medium text-[#6b7280]">
                      {app.status === "beta" ? "BETA" : "ACTIVE"}
                    </div>
                  </div>
                  <div className="mt-2 text-sm text-[#4b5563]">{app.summary}</div>
                </Link>
              ))}
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}
