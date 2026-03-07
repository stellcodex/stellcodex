import { ReactNode } from "react";
import { MasterFrame } from "@/components/layout/MasterFrame";

export function LayoutShell({ children }: { children: ReactNode }) {
  return (
    <MasterFrame>
      <div className="mx-auto w-full max-w-6xl px-4 py-6 sm:py-8">
        <div className="rounded-2xl border border-[#d7d3c8] bg-white/90 p-4 shadow-sm sm:p-5">
          {children}
        </div>
      </div>
    </MasterFrame>
  );
}
