import test from "node:test";
import { collectSourceFiles, readSource } from "../helpers/sourceTestUtils";

test("frontend UI surfaces do not leak storage internals", () => {
  const files = collectSourceFiles(["app", "components", "lib"]);
  const forbidden = [/\bstorage_key\b/i, /\bobject_key\b/i, /\bbucket\b/i, /\bprovider[_\s-]?url\b/i];
  const allowedDefinitions = new Set(["lib/utils/noLeak.ts"]);

  for (const file of files) {
    if (allowedDefinitions.has(file)) continue;
    const source = readSource(file);
    for (const pattern of forbidden) {
      if (pattern.test(source)) {
        throw new Error(`${file} contains forbidden token ${pattern}`);
      }
    }
  }
});
