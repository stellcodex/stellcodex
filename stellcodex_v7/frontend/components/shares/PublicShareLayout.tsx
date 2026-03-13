import type { ReactNode } from "react";

export interface PublicShareLayoutProps {
  title: string;
  meta?: ReactNode;
  children: ReactNode;
}

export function PublicShareLayout({ title, meta, children }: PublicShareLayoutProps) {
  return (
    <div className="viewer-shell">
      <section className="viewer-frame">
        <div className="viewer-card">
          <div className="eyebrow">Public share</div>
          <h1 className="page-title">{title}</h1>
          {meta}
        </div>
        {children}
      </section>
    </div>
  );
}
