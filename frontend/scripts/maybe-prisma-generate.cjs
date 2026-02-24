#!/usr/bin/env node
const { spawnSync } = require("node:child_process");

function hasModule(name) {
  try {
    require.resolve(name);
    return true;
  } catch {
    return false;
  }
}

if (!hasModule("prisma")) {
  console.log("[info] prisma package not installed yet; skipping prisma generate");
  process.exit(0);
}

const cmd = process.platform === "win32" ? "npx.cmd" : "npx";
const result = spawnSync(cmd, ["prisma", "generate"], { stdio: "inherit" });
process.exit(result.status || 0);

