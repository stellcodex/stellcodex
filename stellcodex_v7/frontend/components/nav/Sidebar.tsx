"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useUser } from "@/context/UserContext";
import { applications } from "@/data/applications";
import { tokens } from "@/lib/tokens";

const primaryLinks = [
  { label: "Dashboard", href: "/dashboard" },
  { label: "My Files", href: "/dashboard/files" },
  { label: "Apps", href: "/apps" },
  { label: "Settings", href: "/dashboard/settings" },
];

const adminLinks = [
  { label: "Users", href: "/admin/users" },
  { label: "Files", href: "/admin/files" },
  { label: "Shares", href: "/admin/shares" },
  { label: "Queues", href: "/admin/queue" },
  { label: "Health", href: "/admin/system" },
  { label: "Audit", href: "/admin/audit" },
  { label: "AI Insights", href: "/admin/ai" },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user } = useUser();
  const activeClass = "bg-[#0c3b3a] text-white";
  const idleClass = "text-[#4f6f6b] hover:bg-[#f3f2ee]";
  return (
    <div className="flex h-screen flex-col gap-sp3 border-r-soft bg-surface px-pagePad py-sp3">
      <Link href="/" className="flex items-center gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#0c3b3a] text-sm font-semibold text-white">
          SC
        </div>
        <span style={tokens.typography.h2} className="text-[#0c2a2a]">STELLCODEX</span>
      </Link>
      <div className="flex flex-col gap-sp1">
        {primaryLinks.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`rounded-lg px-3 py-2 text-sm font-medium ${active ? activeClass : idleClass}`}
            >
              {item.label}
            </Link>
          );
        })}
      </div>
      {user.role === "admin" ? (
        <>
          <div className="mt-sp2 text-xs font-semibold uppercase tracking-[0.18em] text-[#8a9895]">
            Admin
          </div>
          <div className="flex flex-col gap-sp1">
            {adminLinks.map((item) => (
              <Link key={item.href} href={item.href} className="text-sm text-[#0c2a2a]">
                {item.label}
              </Link>
            ))}
          </div>
        </>
      ) : null}
      <div className="mt-sp2 text-xs font-semibold uppercase tracking-[0.18em] text-[#8a9895]">
        Applications
      </div>
      <div className="flex flex-col gap-sp1">
        {applications.map((item) => (
          <Link key={item.href} href={item.href} className="flex items-center gap-2 text-sm text-[#0c2a2a]">
            <span className="text-base">{item.icon}</span>
            <span>{item.label}</span>
          </Link>
        ))}
      </div>
    </div>
  );
}
