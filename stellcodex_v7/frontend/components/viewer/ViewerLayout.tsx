import type { ReactNode } from "react";

export interface ViewerLayoutProps {
  toolbar: ReactNode;
  left: ReactNode;
  center: ReactNode;
  right: ReactNode;
}

export function ViewerLayout({ toolbar, left, center, right }: ViewerLayoutProps) {
  return (
    <div className="sc-stack">
      {toolbar}
      <div className="sc-viewer-layout">
        {left}
        {center}
        {right}
      </div>
    </div>
  );
}
