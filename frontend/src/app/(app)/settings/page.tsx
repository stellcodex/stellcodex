import { SettingsScreen } from "@/components/settings/SettingsScreen";
import { requireWorkspaceSession } from "@/lib/server/auth";

export default async function SettingsPage() {
  const session = await requireWorkspaceSession();
  return <SettingsScreen initialSession={session} />;
}
