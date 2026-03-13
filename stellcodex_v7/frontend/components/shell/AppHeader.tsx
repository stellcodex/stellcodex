import type { ReactNode } from "react";

type AppHeaderProps = {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
};

export function AppHeader({ title, subtitle, actions }: AppHeaderProps) {
  return (
    <header className="sc-header">
      <div className="sc-stack">
        <strong>{title}</strong>
        {subtitle ? <span className="sc-muted">{subtitle}</span> : null}
      </div>
      {actions}
    </header>
  );
}
