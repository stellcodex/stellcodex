"use client";

import Link from "next/link";
import type { ReactNode } from "react";

// Auth routes share one visual contract so login, register, and recovery stay
// readable and predictable across web and app-store distributions.
export const authInputClassName =
  "w-full rounded-2xl border border-[#d7dfde] bg-white px-4 py-3 text-sm text-[#111827] outline-none transition focus:border-[#0f766e] focus:ring-2 focus:ring-[#b7d9d5]";

export const authPrimaryButtonClassName =
  "w-full rounded-2xl bg-[#0f766e] py-3 text-sm font-semibold text-white transition hover:bg-[#0c5f59] active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-60";

export function AuthShell({
  eyebrow,
  title,
  description,
  footer,
  children,
}: {
  eyebrow: string;
  title: string;
  description: string;
  footer?: ReactNode;
  children: ReactNode;
}) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[#f5f7f6] px-4 py-10 text-[#111827]">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <Link href="/" className="inline-flex items-center gap-3 rounded-full border border-[#d7dfde] bg-white px-4 py-2 shadow-sm">
            <span className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-[#e8f3f1] text-sm font-semibold text-[#0f766e]">
              SC
            </span>
            <span className="text-lg font-semibold tracking-[0.12em] text-[#111827]">STELLCODEX</span>
          </Link>
        </div>

        <section className="rounded-[28px] border border-[#d7dfde] bg-white p-8 shadow-[0_20px_60px_rgba(15,23,42,0.08)]">
          <div className="text-[11px] font-semibold uppercase tracking-[0.28em] text-[#0f766e]">{eyebrow}</div>
          <h1 className="mt-3 text-2xl font-semibold tracking-tight text-[#111827]">{title}</h1>
          <p className="mt-2 text-sm leading-6 text-[#4b5563]">{description}</p>
          <div className="mt-8">{children}</div>
          {footer ? <div className="mt-8 border-t border-[#e5eceb] pt-6 text-center text-sm text-[#4b5563]">{footer}</div> : null}
        </section>
      </div>
    </main>
  );
}
