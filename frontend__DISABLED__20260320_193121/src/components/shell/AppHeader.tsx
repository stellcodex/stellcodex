"use client";

import { useRouter } from "next/navigation";

import { Button } from "@/components/primitives/Button";
import { DropdownMenu } from "@/components/primitives/DropdownMenu";
import { SearchInput } from "@/components/primitives/SearchInput";
import { logout } from "@/lib/api/auth";

export interface AppHeaderProps {
  userLabel: string;
  userRole: string;
}

export function AppHeader({ userLabel, userRole }: AppHeaderProps) {
  const router = useRouter();

  async function handleLogout() {
    await logout().catch(() => undefined);
    router.refresh();
    router.push("/sign-in");
  }

  return (
    <header className="sticky top-0 z-[var(--z-sticky)] border-b border-[var(--border-muted)] bg-white px-5 py-4">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="w-full max-w-xl">
          <SearchInput aria-label="Search workspaces" placeholder="Search projects or file IDs" />
        </div>
        <div className="flex items-center gap-3">
          <Button onClick={() => router.push("/dashboard")} variant="secondary">
            Upload
          </Button>
          <DropdownMenu
            items={[
              { id: "settings", label: "Settings", onSelect: () => router.push("/settings") },
              { id: "logout", label: "Logout", onSelect: () => void handleLogout() },
            ]}
            label={`${userLabel} · ${userRole}`}
          />
        </div>
      </div>
    </header>
  );
}
