"use client";

import { ConfirmActionDialog } from "@/components/primitives/ConfirmActionDialog";

export interface ShareRevokeDialogProps {
  open: boolean;
  busy?: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}

export function ShareRevokeDialog({ open, busy = false, onCancel, onConfirm }: ShareRevokeDialogProps) {
  return (
    <ConfirmActionDialog
      open={open}
      title="Revoke share"
      description="This share will become unavailable immediately."
      confirmLabel="Revoke"
      busy={busy}
      onCancel={onCancel}
      onConfirm={onConfirm}
    />
  );
}
