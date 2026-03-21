import { ProjectWorkspace } from "@/components/product/ProjectWorkspace";

export default async function ProjectDetailPage({ params }: { params: Promise<{ projectId: string }> }) {
  const { projectId } = await params;
  return <ProjectWorkspace projectId={projectId} />;
}
