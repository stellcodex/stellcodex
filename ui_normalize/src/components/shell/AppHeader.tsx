"use client";

import * as React from "react";
import { usePathname, useRouter } from "next/navigation";

import { DropdownMenu } from "@/components/primitives/DropdownMenu";
import { logout } from "@/lib/api/auth";

function getRouteContext(pathname: string) {
  const segments = pathname.split("/").filter(Boolean);

  if (segments.length === 0 || segments[0] === "dashboard") {
    return {
      title: "Dashboard",
    };
  }

  if (segments[0] === "projects" && segments.length === 1) {
    return {
      title: "Projects",
    };
  }

  if (segments[0] === "projects" && segments[1]) {
    return {
      title: "Project",
    };
  }

  if (segments[0] === "viewer") {
    return {
      title: "Viewer",
    };
  }

  if (segments[0] === "files" && segments[1] && segments[2] === "viewer") {
    return {
      title: "Viewer",
    };
  }

  if (segments[0] === "files" && segments[1]) {
    return {
      title: "File",
    };
  }

  if (segments[0] === "settings") {
    return {
      title: "Settings",
    };
  }

  if (segments[0] === "admin") {
    return {
      title: "Admin",
    };
  }

  return {
    title: "Workspace",
  };
}

export interface AppHeaderProps {
  userLabel: string;
}

export function AppHeader({ userLabel }: AppHeaderProps) {
  const router = useRouter();
  const pathname = usePathname();
  const context = React.useMemo(() => getRouteContext(pathname), [pathname]);

  async function handleLogout() {
    await logout().catch(() => undefined);
    window.location.assign("/sign-in");
  }

  return (
    <header className="sticky top-0 z-[var(--z-sticky)] border-b border-[#eee] bg-white">
      <div className="flex items-center justify-between gap-4 px-4 py-4 lg:px-6">
        <div className="min-w-0">
          <div className="text-[18px] font-semibold text-[var(--foreground-strong)]">{context.title}</div>
        </div>

        <div className="flex items-center gap-2">
          <DropdownMenu
            items={[
              { id: "settings", label: "Settings", onSelect: () => router.push("/settings") },
              { id: "logout", label: "Logout", onSelect: () => void handleLogout() },
            ]}
            label={userLabel}
          />
        </div>
      </div>
    </header>
  );
}
