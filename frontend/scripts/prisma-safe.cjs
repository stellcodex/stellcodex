#!/usr/bin/env node
const { spawnSync } = require("node:child_process");

const args = process.argv.slice(2);
if (!args.length) {
  console.error("Usage: node scripts/prisma-safe.cjs <prisma args...>");
  process.exit(1);
}

function hasModule(name) {
  try {
    require.resolve(name);
    return true;
  } catch {
    return false;
  }
}

if (!hasModule("prisma")) {
  console.error("[error] prisma package is not installed. Run: npm install prisma @prisma/client");
  process.exit(1);
}

const cmd = process.platform === "win32" ? "npx.cmd" : "npx";
const result = spawnSync(cmd, ["prisma", ...args], { stdio: "inherit" });
process.exit(result.status || 0);

