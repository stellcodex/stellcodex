import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const scopes = [
  "app/files",
  "app/projects",
  "app/settings",
  "app/s",
  "app/(app)/shares",
  "app/(app)/admin",
  "components/admin",
  "components/dashboard",
  "components/files",
  "components/intelligence",
  "components/primitives",
  "components/projects",
  "components/share",
  "components/shares",
  "components/shell",
  "components/status",
  "components/viewer/AssemblyTree.tsx",
  "components/viewer/AssemblyTreeNode.tsx",
  "components/viewer/FitControls.tsx",
  "components/viewer/SelectionInspector.tsx",
  "components/viewer/TreeSearch.tsx",
  "components/viewer/ViewerCanvas.tsx",
  "components/viewer/ViewerErrorState.tsx",
  "components/viewer/ViewerLayout.tsx",
  "components/viewer/ViewerLoadingState.tsx",
  "components/viewer/ViewerProcessingState.tsx",
  "components/viewer/ViewerToolbar.tsx",
  "components/viewer/ViewerUnavailableState.tsx",
  "components/viewer/VisibilityControls.tsx",
  "lib/api",
  "lib/config",
  "lib/contracts",
  "lib/hooks",
  "lib/mappers",
  "lib/store",
  "lib/utils",
  "styles",
];

const banned = [
  { pattern: /\bstorage_key\b/i, message: "storage_key leak" },
  { pattern: /\bobject_key\b/i, message: "object_key leak" },
  { pattern: /\brevision_id\b/i, message: "revision_id leak" },
  { pattern: /\bbucket\b/i, message: "bucket leak" },
  { pattern: /\bprovider[_\s-]?url\b/i, message: "provider URL leak" },
];

function walk(entry) {
  const absolute = path.join(root, entry);
  if (!fs.existsSync(absolute)) return [];
  const stats = fs.statSync(absolute);
  if (stats.isFile()) return [absolute];
  return fs.readdirSync(absolute, { withFileTypes: true }).flatMap((item) => walk(path.join(entry, item.name)));
}

const files = scopes
  .flatMap((entry) => walk(entry))
  .filter((file) => /\.(ts|tsx|css|mjs)$/.test(file));

const issues = [];
const allowedDefinitions = new Set([path.join(root, "lib/utils/noLeak.ts")]);

for (const file of files) {
  if (allowedDefinitions.has(file)) continue;
  const body = fs.readFileSync(file, "utf8");
  for (const rule of banned) {
    if (rule.pattern.test(body)) {
      issues.push(`${path.relative(root, file)}: ${rule.message}`);
    }
  }
}

if (issues.length > 0) {
  console.error("UI lint failed:");
  for (const issue of issues) {
    console.error(`- ${issue}`);
  }
  process.exit(1);
}

console.log(`UI lint passed for ${files.length} files.`);
