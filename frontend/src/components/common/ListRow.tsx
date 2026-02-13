import Link from "next/link";

type ListRowProps = {
  title: string;
  subtitle?: string;
  href?: string;
  trailing?: string;
};

export function ListRow({ title, subtitle, href, trailing }: ListRowProps) {
  const content = (
    <div className="flex h-rowH items-center justify-between gap-sp2 px-cardPad">
      <div className="flex flex-col">
        <span className="text-fs1 text-text">{title}</span>
        {subtitle ? <span className="text-fs0 text-muted">{subtitle}</span> : null}
      </div>
      {trailing ? <span className="text-fs0 text-muted2">{trailing}</span> : null}
    </div>
  );

  if (href) {
    return (
      <Link href={href} className="block border-soft rounded-r1 bg-surface">
        {content}
      </Link>
    );
  }

  return <div className="border-soft rounded-r1 bg-surface">{content}</div>;
}
