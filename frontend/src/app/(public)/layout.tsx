import type { ReactNode } from "react";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";

export default function PublicLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-[#f3f2ee] text-[#0c2a2a]">
      <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute -top-40 right-[-10%] h-[520px] w-[520px] rounded-full bg-[radial-gradient(circle,rgba(53,118,113,0.28),rgba(243,242,238,0))]" />
        <div className="absolute -bottom-32 left-[-8%] h-[460px] w-[460px] rounded-full bg-[radial-gradient(circle,rgba(226,144,43,0.22),rgba(243,242,238,0))]" />
        <div className="absolute inset-x-0 top-0 h-40 bg-[linear-gradient(180deg,rgba(12,59,58,0.08),rgba(243,242,238,0))]" />
      </div>

      <SiteHeader />
      <main>{children}</main>
      <SiteFooter />
    </div>
  );
}
