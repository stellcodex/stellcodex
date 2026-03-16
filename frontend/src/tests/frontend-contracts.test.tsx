import assert from "node:assert/strict";
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
import type { RawFileDetail } from "../lib/contracts/files";
import type { DecisionRecord } from "../lib/contracts/ui";
import { mapAdminAudit } from "../lib/mappers/adminMappers";
import { countOccurrenceNodes, mapFileRecord, mapViewerModel } from "../lib/mappers/fileMappers";
import { mapPublicShareTerminalState } from "../lib/mappers/shareMappers";

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
