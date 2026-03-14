import { getFile, getFileManifest } from "@/lib/api/files";

export async function getViewerFile(fileId: string) {
  return getFile(fileId);
}

export async function getViewerManifest(fileId: string) {
  return getFileManifest(fileId);
}
