import { WorkspaceRedirect } from "@/components/workspace/WorkspaceRedirect";

export default async function AppRunnerPage({
  params,
}: {
  params: Promise<{ appId: string }>;
}) {
  const { appId } = await params;
  return <WorkspaceRedirect suffix={`/app/${appId}`} preserveSearch />;
}
