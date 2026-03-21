const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");

function run(cmd, cwd) {
  return execSync(cmd, {
    cwd,
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
  }).trim();
}

function tryRun(cmd, cwd) {
  try {
    return run(cmd, cwd);
  } catch (_err) {
    return null;
  }
}

function resolveGitMetadata(frontendDir, repoDir) {
  const candidates = [
    process.env.STELLCODEX_BUILD_REPO,
    repoDir,
    frontendDir,
  ].filter(Boolean);

  for (const candidate of candidates) {
    const topLevel = tryRun("git rev-parse --show-toplevel", candidate);
    if (!topLevel) continue;

    const commit = tryRun("git rev-parse HEAD", topLevel);
    const branch =
      tryRun("git branch --show-current", topLevel) ||
      tryRun("git rev-parse --abbrev-ref HEAD", topLevel) ||
      "unknown";

    if (commit) {
      return {
        repoPath: topLevel,
        branch,
        commit,
      };
    }
  }

  const commit =
    process.env.STELLCODEX_BUILD_COMMIT ||
    process.env.GIT_COMMIT ||
    "unknown";
  const branch =
    process.env.STELLCODEX_BUILD_BRANCH ||
    process.env.GIT_BRANCH ||
    "unknown";

  return {
    repoPath: process.env.STELLCODEX_BUILD_REPO || repoDir,
    branch,
    commit,
  };
}

const frontendDir = path.resolve(__dirname, "..");
const repoDir = path.resolve(frontendDir, "..");
const outPath = path.join(frontendDir, "public", "build_id.txt");

const { repoPath, branch, commit } = resolveGitMetadata(frontendDir, repoDir);
const timestamp = execSync("TZ=Europe/Istanbul date --iso-8601=seconds", {
  encoding: "utf8",
  stdio: ["ignore", "pipe", "pipe"],
}).trim();

const body = [
  "repo=stellcodex",
  `repo_path=${repoPath}`,
  `branch=${branch}`,
  `commit=${commit}`,
  `commit_short=${commit === "unknown" ? "unknown" : commit.slice(0, 7)}`,
  `generated_at=${timestamp}`,
  "",
].join("\n");

fs.writeFileSync(outPath, body, "utf8");
process.stdout.write(`Wrote ${outPath}\n`);
