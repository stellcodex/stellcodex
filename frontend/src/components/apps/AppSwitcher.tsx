"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useScxContext, withScxContext } from "../common/useScxContext";
import { applications } from "@/data/applications";

export function AppSwitcher() {
  const pathname = usePathname();
  const context = useScxContext();
  return (
    <div className="flex items-center gap-sp1 rounded-r1 border-soft bg-surface px-sp1 py-sp1">
      {applications.map((app) => {
        const active = pathname === app.href;
        return (
          <Link
            key={app.href}
            href={withScxContext(app.href, context)}
            className={`rounded-r0 px-sp2 py-sp1 text-fs0 ${active ? "bg-accentWeak text-text" : "text-muted"}`}
          >
            {app.shortLabel}
          </Link>
        );
      })}
    </div>
  );
}
