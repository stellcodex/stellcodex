import { notFound } from "next/navigation";
import { PlatformClient } from "@/components/platform/PlatformClient";
import { WorkspaceOpenRoute } from "@/components/workspace/WorkspaceOpenRoute";

type WorkspaceParams = {
  workspaceId: string;
  slug?: string[];
};

export default async function WorkspacePage({
  params,
}: {
  params: Promise<WorkspaceParams>;
}) {
  const { workspaceId, slug = [] } = await params;

  if (!workspaceId) {
    notFound();
  }

  const [section, resourceId, extra] = slug;
  if (extra) {
    notFound();
  }

  if (!section) return <PlatformClient view="home" />;
  if (section === "files") return <PlatformClient view="files" />;
  if (section === "library") return <PlatformClient view="library" />;
  if (section === "settings") return <PlatformClient view="settings" />;
  if (section === "admin") return <PlatformClient view="admin" />;
  if (section === "projects") {
    return resourceId ? <PlatformClient view="project" projectId={resourceId} /> : <PlatformClient view="projects" />;
  }
  if (section === "app" && resourceId) {
    return <PlatformClient view="app" appId={resourceId} />;
  }
  if (section === "open" && resourceId) {
    return <WorkspaceOpenRoute fileId={resourceId} />;
  }

  notFound();
}
