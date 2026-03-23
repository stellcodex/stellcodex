import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import * as React from "react";
import { renderToStaticMarkup } from "react-dom/server";

import { AdminAuditTable } from "../components/admin/AdminAuditTable";
import { AdminHealthPanel } from "../components/admin/AdminHealthPanel";
import { AdminQueuesTable } from "../components/admin/AdminQueuesTable";
import { AttentionPanel } from "../components/dashboard/AttentionPanel";
import { UploadDropzone } from "../components/dashboard/UploadDropzone";
import { FileMetaCard } from "../components/files/FileMetaCard";
import { VersionsTable } from "../components/files/VersionsTable";
import { WorkflowSummaryCard } from "../components/files/WorkflowSummaryCard";
import { ApprovalPanel } from "../components/intelligence/ApprovalPanel";
import { DecisionPanel } from "../components/intelligence/DecisionPanel";
import { ProjectFilesTable } from "../components/projects/ProjectFilesTable";
import { ViewerIntelligencePanel } from "../components/product/ViewerIntelligencePanel";
import { shouldHandleSessionExpiry } from "../lib/api/fetch";
import { sanitizeNextPath } from "../lib/auth/session";
import { appShellRootClassName } from "../components/shell/AppShell";
import { getSidebarWidthClass, sidebarActiveItemClassName } from "../components/shell/AppSidebar";
import type { RawFileDetail } from "../lib/contracts/files";
import type { DecisionRecord } from "../lib/contracts/ui";
import { mapAdminAudit } from "../lib/mappers/adminMappers";
import { mapSessionUser } from "../lib/mappers/authMappers";
import { countOccurrenceNodes, mapFileRecord, mapViewerModel } from "../lib/mappers/fileMappers";
import { mapPublicShareRecord, mapPublicShareTerminalState } from "../lib/mappers/shareMappers";

const frontendRoot = path.resolve(__dirname, "..");
const appRoot = path.join(frontendRoot, "app");

const rawFile: RawFileDetail = {
  file_id: "scx_test-file-id",
  original_name: "fixture.step",
  kind: "3d",
  mode: "brep",
  created_at: "2026-03-16T12:00:00Z",
  content_type: "model/step",
  size_bytes: 4096,
  status: "ready",
  visibility: "private",
  thumbnail_url: null,
  preview_url: null,
  preview_urls: [],
  gltf_url: "/api/v1/files/scx_test-file-id/gltf",
  original_url: "/api/v1/files/scx_test-file-id/content",
  part_count: 3,
  error: null,
};

const decision: DecisionRecord = {
  sessionId: "session-id",
  fileId: "scx_test-file-id",
  stateCode: "S5",
  stateLabel: "Awaiting Approval",
  approvalRequired: true,
  riskFlags: ["draft_below_min"],
  manufacturingMethod: "cnc",
  mode: "brep",
  confidence: 0.83,
  ruleVersion: "v1.2.3",
  explanations: [
    {
      ruleId: "DRAFT_BELOW_MIN",
      triggered: true,
      severity: "HIGH",
      reference: "rule_configs:draft_below_min",
      reasoning: "Minimum draft is below threshold.",
    },
  ],
};

function readAllSourceFiles(root: string): string {
  const entries = fs.readdirSync(root, { withFileTypes: true });
  return entries
    .flatMap((entry) => {
      const nextPath = path.join(root, entry.name);
      if (entry.isDirectory()) {
        return readAllSourceFiles(nextPath);
      }
      if (!/\.(ts|tsx|css)$/.test(entry.name)) {
        return "";
      }
      return fs.readFileSync(nextPath, "utf8");
    })
    .join("\n");
}

function readWorkspaceSource() {
  return [
    path.join(frontendRoot, "app"),
    path.join(frontendRoot, "components"),
    path.join(frontendRoot, "lib"),
    path.join(frontendRoot, "styles"),
  ]
    .map((segment) => readAllSourceFiles(segment))
    .join("\n");
}

const checks: Array<[string, () => void | Promise<void>]> = [
  ["public-file-identity", () => {
  const mapped = mapFileRecord({
    ...rawFile,
    revision_id: "internal-revision",
    storage_key: "s3/private/object",
  } as typeof rawFile & { revision_id: string; storage_key: string });

  const serialized = JSON.stringify(mapped);
  assert.equal(mapped.fileId, rawFile.file_id);
  assert.equal("revision_id" in (mapped as unknown as Record<string, unknown>), false);
  assert.equal(serialized.includes("internal-revision"), false);
  assert.equal(serialized.includes("storage_key"), false);
  }],

  ["no-storage-leak", () => {
  const mapped = mapAdminAudit({
    id: "audit-1",
    event_type: "share.created",
    actor_user_id: "user-1",
    actor_anon_sub: null,
    file_id: "scx_test-file-id",
    created_at: "2026-03-16T12:00:00Z",
    data: {
      bucket: "private-bucket",
      object_key: "secret/path",
      storage_key: "secret/path-2",
      safe: "value",
    },
  });

  assert.deepEqual(mapped.data, { safe: "value" });
  }],

  ["viewer-occurrence-count", () => {
  const count = countOccurrenceNodes([
    {
      id: "assembly-1",
      occurrenceId: "assembly-1",
      partId: "assembly-1",
      label: "Assembly",
      kind: "assembly",
      partCount: 0,
      gltfNodes: [],
      children: [
        {
          id: "occ-1",
          occurrenceId: "occ-1",
          partId: "part-1",
          label: "Part 1",
          kind: "part",
          partCount: 1,
          gltfNodes: ["mesh-a", "mesh-b", "mesh-c"],
          children: [],
        },
        {
          id: "occ-2",
          occurrenceId: "occ-2",
          partId: "part-2",
          label: "Part 2",
          kind: "part",
          partCount: 1,
          gltfNodes: ["mesh-d"],
          children: [],
        },
      ],
    },
  ]);

  assert.equal(count, 2);
  }],

  ["assembly-meta-required", () => {
  const viewer = mapViewerModel({
    file: rawFile,
    status: {
      state: "succeeded",
      derivatives_available: ["gltf", "thumbnail"],
      progress_hint: "ready",
      progress_percent: 100,
    },
    manifest: {
      model_id: "scx_test-file-id",
      assembly_tree: [],
    },
  });

  assert.equal(viewer.state, "metadata_missing");
  }],

  ["share-expiry-410", () => {
  assert.equal(mapPublicShareTerminalState(410), "expired");
  }],

  ["share-revoke", () => {
  assert.equal(mapPublicShareTerminalState(403), "revoked");
  }],

  ["public-share-no-file-identity", () => {
  const mapped = mapPublicShareRecord({
    status: "ready",
    permission: "view",
    can_view: true,
    can_download: false,
    expires_at: "2026-03-16T12:00:00Z",
    content_type: "model/gltf-binary",
    original_filename: "fixture.glb",
    size_bytes: 1024,
    gltf_url: "/api/v1/share/token/gltf",
    original_url: null,
    file_id: "scx_hidden-id",
  } as {
    status: string;
    permission: string;
    can_view: boolean;
    can_download: boolean;
    expires_at: string;
    content_type: string;
    original_filename: string;
    size_bytes: number;
    gltf_url: string;
    original_url: null;
    file_id: string;
  });

  const serialized = JSON.stringify(mapped);
  assert.equal(serialized.includes("scx_hidden-id"), false);
  }],

  ["session-role-mapping", () => {
  const mapped = mapSessionUser({
    authenticated: true,
    role: "member",
    user: {
      id: "user-1",
      email: "member@example.com",
      full_name: "Member User",
      role: "member",
      auth_provider: "google",
      is_active: true,
      created_at: "2026-03-16T12:00:00Z",
      last_login_at: "2026-03-16T12:00:00Z",
    },
  });

  assert.deepEqual(mapped, {
    label: "Member User",
    role: "member",
    email: "member@example.com",
    fullName: "Member User",
    authProvider: "google",
  });
  }],

  ["sign-in-route-contract", () => {
  assert.equal(fs.existsSync(path.join(appRoot, "(public)", "sign-in", "page.tsx")), true);
  assert.equal(fs.existsSync(path.join(appRoot, "(public)", "settings", "page.tsx")), false);
  assert.equal(fs.existsSync(path.join(appRoot, "(app)", "settings", "page.tsx")), true);

  const rootPageSource = fs.readFileSync(path.join(appRoot, "page.tsx"), "utf8");
  const authSource = fs.readFileSync(path.join(frontendRoot, "lib", "server", "auth.ts"), "utf8");
  const proxySource = fs.readFileSync(path.join(frontendRoot, "proxy.ts"), "utf8");
  assert.equal(rootPageSource.includes('"/sign-in"') || rootPageSource.includes("SIGN_IN_ROUTE"), true);
  assert.equal(rootPageSource.includes('"/settings"'), false);
  assert.equal(authSource.includes('redirect("/settings")'), false);
  assert.equal(authSource.includes("SIGN_IN_ROUTE"), true);
  assert.equal(proxySource.includes("SIGN_IN_ROUTE"), true);
  assert.equal(proxySource.includes("/settings"), true);
  assert.equal(fs.existsSync(path.join(frontendRoot, "middleware.ts")), false);
  }],

  ["route-structure-contract", () => {
  assert.equal(fs.existsSync(path.join(appRoot, "(app)", "dashboard", "page.tsx")), true);
  assert.equal(fs.existsSync(path.join(appRoot, "(app)", "projects", "page.tsx")), true);
  assert.equal(fs.existsSync(path.join(appRoot, "(app)", "projects", "[projectId]", "page.tsx")), true);
  assert.equal(fs.existsSync(path.join(appRoot, "(app)", "files", "[fileId]", "page.tsx")), true);
  assert.equal(fs.existsSync(path.join(appRoot, "(app)", "files", "[fileId]", "viewer", "page.tsx")), true);
  assert.equal(fs.existsSync(path.join(appRoot, "(app)", "shares", "page.tsx")), true);
  assert.equal(fs.existsSync(path.join(appRoot, "(app)", "admin", "page.tsx")), true);
  assert.equal(fs.existsSync(path.join(appRoot, "(app)", "settings", "page.tsx")), true);
  assert.equal(fs.existsSync(path.join(appRoot, "(share)", "s", "[token]", "page.tsx")), true);
  }],

  ["safe-next-path-contract", () => {
  assert.equal(sanitizeNextPath("/dashboard"), "/dashboard");
  assert.equal(sanitizeNextPath("https://stellcodex.com/projects"), "/projects");
  assert.equal(sanitizeNextPath("//evil.example.com"), null);
  assert.equal(sanitizeNextPath("/sign-in"), null);
  }],

  ["session-expiry-routing-contract", () => {
  assert.equal(shouldHandleSessionExpiry("/projects", 401), true);
  assert.equal(shouldHandleSessionExpiry("/files/scx_test-file-id", 403), true);
  assert.equal(shouldHandleSessionExpiry("/auth/login", 401), false);
  assert.equal(shouldHandleSessionExpiry("/auth/register", 401), false);
  assert.equal(shouldHandleSessionExpiry("/s/token", 403), false);
  }],

  ["sidebar-collapsible-contract", () => {
  assert.notEqual(getSidebarWidthClass(true), getSidebarWidthClass(false));
  assert.match(getSidebarWidthClass(true), /w-\[/);
  assert.match(getSidebarWidthClass(false), /w-\[/);
  }],

  ["sidebar-active-nav-readable", () => {
  assert.equal(sidebarActiveItemClassName.includes("foreground-strong"), true);
  assert.equal(sidebarActiveItemClassName.includes("accent-foreground"), false);
  assert.equal(sidebarActiveItemClassName.includes("accent-default"), false);
  }],

  ["sidebar-required-sections", () => {
  const sidebarSource = fs.readFileSync(path.join(frontendRoot, "components", "shell", "AppSidebar.tsx"), "utf8");
  for (const label of ["Dashboard", "Projects", "Viewer", "Shares", "Admin", "Settings"]) {
    assert.equal(sidebarSource.includes(label), true);
  }
  }],

  ["white-shell-contract", () => {
  const tokensSource = fs.readFileSync(path.join(frontendRoot, "styles", "tokens.css"), "utf8");
  const globalsSource = fs.readFileSync(path.join(appRoot, "globals.css"), "utf8");
  assert.equal(appShellRootClassName.includes("bg-white"), true);
  assert.match(tokensSource, /--background-canvas:\s*#ffffff/i);
  assert.match(tokensSource, /--background-shell:\s*#ffffff/i);
  assert.equal(globalsSource.includes("radial-gradient"), false);
  assert.match(globalsSource, /background:\s*#ffffff/i);
  }],

  ["no-localstorage-bearer-workspace-dependency", () => {
  const source = readWorkspaceSource();
  assert.equal(source.includes("localStorage"), false);
  assert.equal(source.includes("Authorization"), false);
  assert.equal(source.includes("Bearer "), false);
  }],

  ["decision-panel-fields", () => {
  const html = renderToStaticMarkup(<DecisionPanel decision={decision} />);
  assert.match(html, /Manufacturing method/);
  assert.match(html, /cnc/);
  assert.match(html, /Mode/);
  assert.match(html, /brep/);
  assert.match(html, /Confidence/);
  assert.match(html, /0\.830/);
  assert.match(html, /Rule version/);
  assert.match(html, /v1\.2\.3/);
  }],

  ["approval-state-visibility", () => {
  const requiredHtml = renderToStaticMarkup(
    <ApprovalPanel
      decision={decision}
      onApprove={async () => undefined}
      onReject={async () => undefined}
    />,
  );
  const skippedHtml = renderToStaticMarkup(
    <ApprovalPanel
      decision={{ ...decision, approvalRequired: false }}
      onApprove={async () => undefined}
      onReject={async () => undefined}
    />,
  );

  assert.match(requiredHtml, /Approve/);
  assert.match(requiredHtml, /Reject/);
  assert.match(skippedHtml, /No approval required/);
  }],

  ["project-file-actions", () => {
  const html = renderToStaticMarkup(
    <ProjectFilesTable
      files={[
        {
          fileId: "scx_test-file-id",
          originalFilename: "fixture.step",
          status: "ready",
          kind: "3d",
          mode: "brep",
          createdAt: "2026-03-16T12:00:00Z",
        },
      ]}
      onShare={() => undefined}
    />,
  );

  assert.match(html, /Viewer/);
  assert.match(html, /Share/);
  }],

  ["viewer-intelligence-sections", () => {
  const html = renderToStaticMarkup(
    <ViewerIntelligencePanel
      decision={decision}
      decisionError={null}
      dfm={null}
      dfmError={null}
      fields={[]}
      fileCreatedAt="2026-03-16T12:00:00Z"
      fileStateMessage="Viewer data is ready."
      fileStatus="ready"
      inputsError={null}
      onApprove={async () => undefined}
      onChange={() => undefined}
      onReject={async () => undefined}
      onSubmit={async () => true}
      rerunSupported={false}
      shareCount={1}
      values={{}}
    />,
  );

  assert.match(html, /State/);
  assert.match(html, /Required Inputs/);
  assert.match(html, /Decision/);
  assert.match(html, /Risks/);
  assert.match(html, /DFM Report/);
  assert.match(html, /Activity and evidence/);
  assert.match(html, /Approval/);
  }],

  ["dashboard basic render", () => {
  const html = renderToStaticMarkup(
    <div>
      <UploadDropzone onUpload={async () => undefined} uploads={[]} />
      <AttentionPanel files={[mapFileRecord(rawFile)]} />
    </div>,
  );

  assert.match(html, /Upload intake/);
  assert.match(html, /Attention queue/);
  }],

  ["file detail basic render", () => {
  const html = renderToStaticMarkup(
    <div>
      <FileMetaCard file={mapFileRecord(rawFile)} projectName="Fixture Project" />
      <WorkflowSummaryCard decision={decision} dfm={null} shareCount={1} status="ready" />
      <VersionsTable supported={false} />
    </div>,
  );

  assert.match(html, /File metadata/);
  assert.match(html, /Workflow summary/);
  assert.match(html, /Version history unavailable/);
  }],

  ["admin pages basic render", () => {
  const html = renderToStaticMarkup(
    <div>
      <AdminHealthPanel items={[{ component: "api", status: "ok" }]} />
      <AdminQueuesTable queues={[{ name: "cad", queuedCount: 1, startedCount: 0, failedCount: 0 }]} />
      <AdminAuditTable
        items={[
          {
            id: "audit-1",
            eventType: "upload.created",
            actorUserId: "user-1",
            actorAnonSub: null,
            fileId: "scx_test-file-id",
            data: { safe: "value" },
            createdAt: "2026-03-16T12:00:00Z",
          },
        ]}
      />
    </div>,
  );

  assert.match(html, /Platform health/);
  assert.match(html, /Queue/);
  assert.match(html, /Event/);
  assert.equal(html.includes("private-bucket"), false);
  assert.equal(html.includes("object_key"), false);
  }],

  ["viewer-route-shell-contract", () => {
  const viewerRouteSource = fs.readFileSync(path.join(appRoot, "viewer", "page.tsx"), "utf8");
  assert.equal(viewerRouteSource.includes("AppShell"), true);
  assert.equal(viewerRouteSource.includes("ViewerWorkspace"), true);
  }],

  ["settings-provider-hidden", () => {
  const settingsSource = fs.readFileSync(path.join(frontendRoot, "components", "settings", "SettingsScreen.tsx"), "utf8");
  assert.equal(settingsSource.includes("Auth provider"), false);
  }],

  ["share-surface-no-fake-fallbacks", () => {
  const shareTableSource = fs.readFileSync(path.join(frontendRoot, "components", "shares", "ShareTable.tsx"), "utf8");
  const shareDialogSource = fs.readFileSync(path.join(frontendRoot, "components", "shares", "ShareDialog.tsx"), "utf8");
  assert.equal(shareTableSource.includes('"Derived"'), false);
  assert.equal(shareDialogSource.includes("enabled later"), false);
  assert.equal(shareDialogSource.includes("future comment scope"), false);
  }],

  ["share-inventory-no-arbitrary-cap", () => {
  const useSharesSource = fs.readFileSync(path.join(frontendRoot, "lib", "hooks", "useShares.ts"), "utf8");
  assert.equal(useSharesSource.includes("slice(0, 50)"), false);
  }],
];

async function main() {
  let failures = 0;
  for (const [name, check] of checks) {
    try {
      await check();
      console.log(`ok - ${name}`);
    } catch (error) {
      failures += 1;
      console.error(`not ok - ${name}`);
      console.error(error);
    }
  }

  console.log(`tests: ${checks.length}`);
  if (failures > 0) {
    console.error(`failures: ${failures}`);
    process.exit(1);
  }
}

void main();
