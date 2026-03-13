import test from "node:test";
import { expectIncludes } from "../helpers/sourceTestUtils";

test("file hub keeps upload flow and progress surfaces wired", () => {
  expectIncludes("app/files/page.tsx", ["UploadDropzone", "UploadProgressList", "useUpload", "handleFilesSelected"]);
});
