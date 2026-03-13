import { Button } from "@/components/primitives/Button";
import { Dialog } from "@/components/primitives/Dialog";

type ConfirmActionDialogProps = {
  open: boolean;
  title: string;
  description?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  busy?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
};

export function ConfirmActionDialog({
  open,
  title,
  description,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  busy = false,
  onConfirm,
  onCancel,
}: ConfirmActionDialogProps) {
  return (
    <Dialog open={open} onClose={onCancel}>
      <div className="sc-panel-body sc-stack">
        <strong>{title}</strong>
        {description ? <span className="sc-muted">{description}</span> : null}
        <div className="sc-inline">
          <Button variant="danger" onClick={onConfirm} loading={busy}>
            {confirmLabel}
          </Button>
          <Button onClick={onCancel}>{cancelLabel}</Button>
        </div>
      </div>
    </Dialog>
  );
}
