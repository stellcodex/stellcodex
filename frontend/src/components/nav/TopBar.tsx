"use client";

import Link from "next/link";
import { tokens } from "@/lib/tokens";

export function TopBar() {
  return (
    <div className="sticky top-0 z-10 flex h-rowH items-center justify-between border-b-soft bg-surface px-pagePad">
      <Link href="/" className="flex items-center gap-sp1">
        <div className="flex h-8 w-8 items-center justify-center rounded-r1 bg-accent text-fs0 font-semibold text-white">
          SC
        </div>
        <span className="hidden md:inline" style={tokens.typography.h2}>STELLCODEX</span>
      </Link>
      <Link href="/projects" className="text-sm font-medium text-[#4f6f6b]">
        Projeler
      </Link>
    </div>
  );
}
