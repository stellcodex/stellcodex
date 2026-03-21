import * as React from "react";

import { cn } from "@/lib/utils";

export interface TableProps {
  children: React.ReactNode;
  className?: string;
}

export function Table({ children, className }: TableProps) {
  return (
    <div className={cn("overflow-x-auto rounded-[12px] border border-[#eeeeee] bg-white", className)}>
      <table className="min-w-full border-collapse text-sm">{children}</table>
    </div>
  );
}
