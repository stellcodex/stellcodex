"use client";

import * as React from "react";

import { Button } from "./Button";
import { Dialog } from "./Dialog";

export interface ConfirmActionDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  description: string;
  confirmLabel?: string;
}

export function ConfirmActionDialog({
  confirmLabel = "Confirm",
  description,
  onClose,
  onConfirm,
  open,
  title,
}: ConfirmActionDialogProps) {
  return (
    <Dialog description={description} onClose={onClose} open={open} title={title}>
      <div className="flex justify-end gap-3">
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={onConfirm} variant="danger">
          {confirmLabel}
        </Button>
      </div>
    </Dialog>
  );
}
