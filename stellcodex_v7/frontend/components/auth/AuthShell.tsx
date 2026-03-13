import Link from "next/link";

export const authInputClassName = "auth-input";
export const authPrimaryButtonClassName = "button button--primary";

type AuthShellProps = {
  title: string;
  subtitle: string;
  children: React.ReactNode;
};

export function AuthShell({ title, subtitle, children }: AuthShellProps) {
  return (
    <div className="auth-shell">
      <section className="auth-card">
        <div className="auth-grid">
          <div className="hero-card auth-panel">
            <div className="eyebrow">STELLCODEX access</div>
            <h1 className="display-title">{title}</h1>
            <p className="lede">{subtitle}</p>
            <div className="pill-row">
              <span className="pill">Light workspace only</span>
              <span className="pill">Shared suite identity</span>
            </div>
            <div className="hero-actions">
              <Link className="button button--ghost" href="/">
                Suite home
              </Link>
              <Link className="button button--ghost" href="/upload">
                Upload entry
              </Link>
            </div>
          </div>
          <div className="auth-card auth-panel">{children}</div>
        </div>
      </section>
    </div>
  );
}
