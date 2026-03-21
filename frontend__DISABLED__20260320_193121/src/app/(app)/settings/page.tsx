import { SettingsScreen } from "@/components/settings/SettingsScreen";
import { getServerSession } from "@/lib/server/auth";

export default async function SettingsPage() {
  const session = await getServerSession();
  return <SettingsScreen initialSession={session} />;
}
