import { AppShell } from "@/components/shell/AppShell";
import { RouteErrorState } from "@/components/states/RouteErrorState";
import { mapSessionUser } from "@/lib/mappers/authMappers";
import { requireWorkspaceSession } from "@/lib/server/auth";

export default async function ProductLayout({ children }: { children: React.ReactNode }) {
  const session = await requireWorkspaceSession();
  const user = mapSessionUser(session);

  if (!user) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-16">
        <RouteErrorState
          description="Workspace session data is unavailable. Sign in again if this state persists."
          title="Workspace unavailable"
        />
      </main>
    );
  }

  return <AppShell session={user}>{children}</AppShell>;
}
