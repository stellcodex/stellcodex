import { WorkspaceRedirect } from "@/components/workspace/WorkspaceRedirect";

export default async function AppModulePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  return <WorkspaceRedirect suffix={`/app/${slug}`} />;
}
