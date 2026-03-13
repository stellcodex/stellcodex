import type { ReactNode } from "react";

type DialogProps = {
  open: boolean;
  onClose: () => void;
  children: ReactNode;
};

export function Dialog({ open, onClose, children }: DialogProps) {
  if (!open) return null;
  return (
    <div className="sc-dialog-backdrop" onClick={onClose}>
      <div className="sc-dialog" onClick={(event) => event.stopPropagation()}>
        {children}
      </div>
    </div>
  );
}
