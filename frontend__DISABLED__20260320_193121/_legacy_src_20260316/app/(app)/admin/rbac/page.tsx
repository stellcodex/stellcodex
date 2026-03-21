import fs from "fs";
import path from "path";
import { SectionHeader } from "@/components/layout/SectionHeader";

function readFileSafe(filePath: string): string | null {
  try {
    return fs.readFileSync(filePath, "utf-8");
  } catch {
    return null;
  }
}

export default function AdminRbacPage() {
  const root = process.cwd();
  const policyPath = path.join(root, "..", "security", "rbac.policy.json");
  const apiPermsPath = path.join(root, "..", "backend", "app", "security", "api-perms.generated.json");
  const criticalPath = path.join(
    root,
    "..",
    "backend",
    "app",
    "security",
    "critical-endpoints.generated.json"
  );
  const routePermsPath = path.join(root, "src", "security", "route-perms.generated.ts");

  const policy = readFileSafe(policyPath);
  const apiPerms = readFileSafe(apiPermsPath);
  const critical = readFileSafe(criticalPath);
  const routePerms = readFileSafe(routePermsPath);

  return (
    <div className="space-y-6">
      <SectionHeader
        title="RBAC"
        description="Read-only policy and generated output files."
        crumbs={[{ label: "Admin", href: "/admin" }, { label: "RBAC" }]}
      />

      <div className="grid gap-4">
        <section className="rounded-2xl border border-slate-200 bg-white p-5">
          <div className="text-sm font-semibold text-slate-900">rbac.policy.json</div>
          <pre className="mt-3 max-h-96 overflow-auto rounded-xl bg-slate-900 p-4 text-xs text-slate-100">
            {policy ?? "File is not available."}
          </pre>
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-5">
          <div className="text-sm font-semibold text-slate-900">api-perms.generated.json</div>
          <pre className="mt-3 max-h-64 overflow-auto rounded-xl bg-slate-900 p-4 text-xs text-slate-100">
            {apiPerms ?? "File is not available."}
          </pre>
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-5">
          <div className="text-sm font-semibold text-slate-900">critical-endpoints.generated.json</div>
          <pre className="mt-3 max-h-64 overflow-auto rounded-xl bg-slate-900 p-4 text-xs text-slate-100">
            {critical ?? "File is not available."}
          </pre>
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-5">
          <div className="text-sm font-semibold text-slate-900">route-perms.generated.ts</div>
          <pre className="mt-3 max-h-64 overflow-auto rounded-xl bg-slate-900 p-4 text-xs text-slate-100">
            {routePerms ?? "File is not available."}
          </pre>
        </section>
      </div>
    </div>
  );
}
