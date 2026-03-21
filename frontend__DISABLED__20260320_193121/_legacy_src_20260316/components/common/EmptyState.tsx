import Link from "next/link";

type EmptyStateProps = {
  title: string;
  description: string;
  primaryCta?: { label: string; href: string };
  secondaryCta?: { label: string; href: string };
};

export function EmptyState({ title, description, primaryCta, secondaryCta }: EmptyStateProps) {
  return (
    <div className="flex flex-col gap-sp2 rounded-r2 border-soft bg-surface px-cardPad py-cardPad">
      <div className="text-fs2 font-semibold text-text">{title}</div>
      <div className="text-fs1 text-muted">{description}</div>
      <div className="flex items-center gap-sp2">
        {primaryCta ? (
          <Link
            href={primaryCta.href}
            className="flex h-btnH items-center justify-center rounded-r1 bg-accent px-sp3 text-fs1 font-medium text-bg"
          >
            {primaryCta.label}
          </Link>
        ) : null}
        {secondaryCta ? (
          <Link
            href={secondaryCta.href}
            className="flex h-btnH items-center justify-center rounded-r1 border-soft bg-surface px-sp3 text-fs1 text-text"
          >
            {secondaryCta.label}
          </Link>
        ) : null}
      </div>
    </div>
  );
}
