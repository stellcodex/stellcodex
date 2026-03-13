export type UploadQueueItem = {
  localId: string;
  fileName: string;
  status: "pending" | "uploading" | "success" | "failed" | "cancelled";
  bytesUploaded: number;
  totalBytes: number;
  fileId?: string | null;
  error?: string | null;
};

let queue: UploadQueueItem[] = [];

export function getUploadQueue() {
  return queue;
}

export function setUploadQueue(next: UploadQueueItem[]) {
  queue = next;
}
