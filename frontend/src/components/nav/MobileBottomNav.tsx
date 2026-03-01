"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const items = [
  { label: "Panel", href: "/dashboard" },
  { label: "Dosyalarım", href: "/dashboard/files" },
  { label: "Ayarlar", href: "/dashboard/settings" },
];

export function MobileBottomNav() {
  const pathname = usePathname();
  return (
    <nav className="fixed bottom-0 left-0 right-0 h-navH border-t-soft bg-surface">
      <div className="flex h-full items-center justify-around px-pagePad">
        {items.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex flex-col items-center gap-sp0 text-xs font-medium ${
                active ? "text-white bg-[#0c3b3a]" : "text-[#4f6f6b]"
              } rounded-lg px-2 py-1`}
            >
              <span className="text-[10px]">•</span>
              <span>{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
