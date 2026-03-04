import { PlatformClient } from "@/components/platform/PlatformClient";

export default async function AppRunnerPage({
  params,
}: {
  params: Promise<{ appId: string }>;
}) {
  const { appId } = await params;
  return <PlatformClient view="app" appId={appId} />;
}
