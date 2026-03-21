import { ViewerWorkspace } from "@/components/product/ViewerWorkspace";
import { AppShell } from "@/components/shell/AppShell";
import { RouteErrorState } from "@/components/states/RouteErrorState";
import { mapSessionUser } from "@/lib/mappers/authMappers";
import { requireWorkspaceSession } from "@/lib/server/auth";

type ViewerPageProps = {
  searchParams: Promise<{
    id?: string | string[];
  }>;
};

export default async function ViewerPage({ searchParams }: ViewerPageProps) {
  const session = await requireWorkspaceSession("/viewer");
  const user = mapSessionUser(session);
  const params = await searchParams;
  const rawId = params.id;
  const fileId = Array.isArray(rawId) ? (rawId[0] ?? "").trim() : (rawId ?? "").trim();

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

  return (
    <AppShell session={user}>
      {fileId ? (
        <ViewerWorkspace fileId={fileId} />
      ) : (
        <div className="mx-auto max-w-[900px] py-6">
          <RouteErrorState
            description="Provide a file_id with /viewer?id={file_id} to open the workstation."
            title="Viewer unavailable"
          />
        </div>
      )}
    </AppShell>
  );
}
