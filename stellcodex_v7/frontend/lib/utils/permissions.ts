export function canDownloadShare(permission?: string | null) {
  return permission === "download";
}

export function canCommentShare(permission?: string | null) {
  return permission === "comment" || permission === "download";
}
