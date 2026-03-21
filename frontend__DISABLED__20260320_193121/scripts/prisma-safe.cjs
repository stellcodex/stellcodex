#!/usr/bin/env node
const { spawnSync } = require("node:child_process");
const fs = require("node:fs");

const args = process.argv.slice(2);

function hasModule(name) {
  try {
    require.resolve(name);
    return true;
  } catch {
    try {
      require.resolve(`${name}/package.json`);
      return true;
    } catch {
      return false;
    }
  }
}

if (!hasModule("prisma")) {
  if (args.length === 0) {
    console.log("[info] prisma package is not installed yet; skipping prisma generate");
    process.exit(0);
  }
  console.error("[error] prisma package is not installed. Run: npm install prisma @prisma/client");
  process.exit(1);
}

const finalArgs = args.length ? args : ["generate"];
if (
  finalArgs.length === 1 &&
  finalArgs[0] === "generate" &&
  !process.env.DATABASE_URL &&
  !fs.existsSync(".env") &&
  !fs.existsSync(".env.local")
) {
  console.log("[info] DATABASE_URL/.env not found; skipping prisma generate");
  process.exit(0);
}

const cmd = process.platform === "win32" ? "npx.cmd" : "npx";
const result = spawnSync(cmd, ["prisma", ...finalArgs], { stdio: "inherit" });
process.exit(result.status || 0);
