import type { ReactNode } from "react";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";

export function MasterFrame({
  children,
  mainClassName,
  showFooter = true,
}: {
  children: ReactNode;
  mainClassName?: string;
  showFooter?: boolean;
}) {
  return (
    <div className="min-h-screen bg-[#f7f7f8] text-[#111827]">
      <SiteHeader />
      <main className={mainClassName}>{children}</main>
      {showFooter ? <SiteFooter /> : null}
    </div>
  );
}
