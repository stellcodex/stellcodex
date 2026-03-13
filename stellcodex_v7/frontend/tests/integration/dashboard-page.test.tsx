import test from "node:test";
import { expectIncludes } from "../helpers/sourceTestUtils";

test("legacy dashboard route remains an intentional redirect", () => {
  expectIncludes("app/(app)/dashboard/page.tsx", ['redirect("/")']);
});
