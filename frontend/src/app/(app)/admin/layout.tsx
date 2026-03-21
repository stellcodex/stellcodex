import { RouteErrorState } from "@/components/states/RouteErrorState";
import { requireWorkspaceSession } from "@/lib/server/auth";

export default async function AdminLayout({ children }: { children: React.ReactNode }) {
  const session = await requireWorkspaceSession();

  if (session.role !== "admin") {
    return (
      <div className="max-w-3xl">
        <RouteErrorState
          description="Admin surfaces are restricted to authenticated admin users."
          title="Admin access denied"
        />
      </div>
    );
  }

  return children;
}
