"use client";

import { Dialog } from "@/components/primitives/Dialog";
import { ShareCreateForm } from "@/components/shares/ShareCreateForm";

export interface ShareDialogProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (value: { fileId: string; permission: "view" | "comment" | "download"; expiresInSeconds: number }) => void;
  defaultFileId?: string;
}

export function ShareDialog({ open, onClose, onSubmit, defaultFileId }: ShareDialogProps) {
  return (
    <Dialog open={open} onClose={onClose}>
      <div className="sc-panel-body sc-stack">
        <strong>Create share</strong>
        <ShareCreateForm onSubmit={onSubmit} defaultFileId={defaultFileId} />
      </div>
    </Dialog>
  );
}
