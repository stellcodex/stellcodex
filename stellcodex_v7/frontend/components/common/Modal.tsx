"use client";

import type { ReactNode } from "react";

export function Modal({
  open,
  title,
  onClose,
  children,
}: {
  open: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
}) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-slate-900/45 p-4">
      <button className="absolute inset-0" aria-label="Kapat" onClick={onClose} />
      <div className="relative z-10 w-full max-w-xl rounded-2xl border border-slate-200 bg-white p-5 shadow-xl">
        <div className="mb-4 flex items-center justify-between gap-4">
          <h2 className="text-base font-semibold text-slate-900">{title}</h2>
          <button
            className="rounded-lg border border-slate-200 px-2 py-1 text-sm text-slate-600 hover:bg-slate-50"
            onClick={onClose}
          >
            Kapat
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

