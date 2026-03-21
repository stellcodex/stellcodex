import { AppShell } from "@/components/shell/AppShell";
import { mapSessionUser } from "@/lib/mappers/authMappers";
import { requireWorkspaceSession } from "@/lib/server/auth";

export default async function ProductLayout({ children }: { children: React.ReactNode }) {
  const session = await requireWorkspaceSession();
  const user = mapSessionUser(session);

  if (!user) {
    return null;
  }

  return <AppShell session={user}>{children}</AppShell>;
}
