import Link from "next/link";

export const revalidate = 1800;
// Public marketing pages refresh on a calm interval.

export default function PublicLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="public-shell">
      <div className="public-frame">
        <header className="public-header">
          <Link className="brand-mark" href="/">
            STELLCODEX
          </Link>
          <nav className="public-nav">
            <Link href="/home">Home</Link>
            <Link href="/features">Features</Link>
            <Link href="/pricing">Pricing</Link>
            <Link href="/docs">Docs</Link>
            <Link href="/upload">Upload</Link>
          </nav>
        </header>
        <main className="public-content">{children}</main>
      </div>
    </div>
  );
}
