import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

const root = process.cwd();

function escapeRegExp(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export function readSource(relativePath: string) {
  return fs.readFileSync(path.join(root, relativePath), "utf8");
}

export function expectIncludes(relativePath: string, patterns: Array<string | RegExp>) {
  const source = readSource(relativePath);
  for (const pattern of patterns) {
    if (typeof pattern === "string") {
      assert.match(source, new RegExp(escapeRegExp(pattern)));
    } else {
      assert.match(source, pattern);
    }
  }
  return source;
}

export function expectExcludes(relativePath: string, patterns: Array<string | RegExp>) {
  const source = readSource(relativePath);
  for (const pattern of patterns) {
    if (typeof pattern === "string") {
      assert.doesNotMatch(source, new RegExp(escapeRegExp(pattern)));
    } else {
      assert.doesNotMatch(source, pattern);
    }
  }
  return source;
}

export function collectSourceFiles(relativePaths: string[]) {
  const files: string[] = [];

  function walk(absolutePath: string, relativePath: string) {
    const stat = fs.statSync(absolutePath);
    if (stat.isFile()) {
      if (/\.(ts|tsx|css|mjs)$/.test(absolutePath)) files.push(relativePath);
      return;
    }
    for (const entry of fs.readdirSync(absolutePath, { withFileTypes: true })) {
      walk(path.join(absolutePath, entry.name), path.join(relativePath, entry.name));
    }
  }

  for (const relativePath of relativePaths) {
    const absolutePath = path.join(root, relativePath);
    if (fs.existsSync(absolutePath)) {
      walk(absolutePath, relativePath);
    }
  }

  return files;
}
