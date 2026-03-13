import type { HTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/utils/cn";

type PanelProps = HTMLAttributes<HTMLDivElement> & {
  title?: string;
  subtitle?: string;
  actions?: ReactNode;
  footer?: ReactNode;
  variant?: "default" | "elevated" | "muted" | "danger";
};

export function Panel({
  title,
  subtitle,
  actions,
  footer,
  children,
  className,
  variant = "default",
  ...props
}: PanelProps) {
  return (
    <section {...props} className={cn("sc-panel", className)} data-variant={variant}>
      {title || subtitle || actions ? (
        <header className="sc-panel-header">
          <div className="sc-page-head">
            <div className="sc-stack">
              {title ? <strong>{title}</strong> : null}
              {subtitle ? <span className="sc-muted">{subtitle}</span> : null}
            </div>
            {actions}
          </div>
        </header>
      ) : null}
      <div className="sc-panel-body">{children}</div>
      {footer ? <footer className="sc-panel-footer">{footer}</footer> : null}
    </section>
  );
}
