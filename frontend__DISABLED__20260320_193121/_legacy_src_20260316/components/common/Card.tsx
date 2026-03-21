import Link from "next/link";

type CardProps = {
  title: string;
  href: string;
  icon?: string;
  subtitle?: string;
};

export function Card({ title, href, icon, subtitle }: CardProps) {
  return (
    <Link
      href={href}
      className="flex flex-none flex-col gap-sp1 rounded-r2 bg-surface border-soft px-cardPad py-cardPad shadow-sh0"
    >
      <div className="flex items-center gap-sp1 text-fs1 text-text">
        <span className="text-fs2 text-icon">{icon || "•"}</span>
        <span className="font-medium">{title}</span>
      </div>
      {subtitle ? <div className="text-fs0 text-muted">{subtitle}</div> : null}
    </Link>
  );
}
