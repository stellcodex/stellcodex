const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");

function run(cmd) {
  return execSync(cmd, {
    cwd: path.resolve(__dirname, ".."),
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
  }).trim();
}

const frontendDir = path.resolve(__dirname, "..");
const repoDir = path.resolve(frontendDir, "..");
const outPath = path.join(frontendDir, "public", "build_id.txt");

const commit = run("git rev-parse HEAD");
const branch = run("git branch --show-current");
const timestamp = execSync("TZ=Europe/Istanbul date --iso-8601=seconds", {
  encoding: "utf8",
  stdio: ["ignore", "pipe", "pipe"],
}).trim();

const body = [
  "repo=stellcodex",
  `repo_path=${repoDir}`,
  `branch=${branch}`,
  `commit=${commit}`,
  `commit_short=${commit.slice(0, 7)}`,
  `generated_at=${timestamp}`,
  "",
].join("\n");

fs.writeFileSync(outPath, body, "utf8");
process.stdout.write(`Wrote ${outPath}\n`);
