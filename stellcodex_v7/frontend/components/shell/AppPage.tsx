import type { ReactNode } from "react";

type AppPageProps = {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
};

export function AppPage({ title, subtitle, actions, children }: AppPageProps) {
  return (
    <section className="sc-page">
      <div className="sc-page-head">
        <div className="sc-stack">
          <h1 className="sc-page-title">{title}</h1>
          {subtitle ? <p className="sc-page-subtitle">{subtitle}</p> : null}
        </div>
        {actions}
      </div>
      {children}
    </section>
  );
}
