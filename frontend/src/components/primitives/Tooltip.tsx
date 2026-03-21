import * as React from "react";

export interface TooltipProps {
  content: string;
  children: React.ReactNode;
}

export function Tooltip({ children, content }: TooltipProps) {
  return <span title={content}>{children}</span>;
}
