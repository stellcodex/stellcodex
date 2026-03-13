import Link from "next/link";

export type BreadcrumbItem = {
  href?: string;
  label: string;
};

export type AppBreadcrumbsProps = {
  items: BreadcrumbItem[];
};

export function AppBreadcrumbs({ items }: AppBreadcrumbsProps) {
  if (items.length === 0) return null;
  return (
    <nav aria-label="Breadcrumbs" className="sc-breadcrumbs">
      {items.map((item, index) => (
        <span key={`${item.label}-${index}`} className="sc-inline">
          {item.href ? <Link href={item.href}>{item.label}</Link> : <span>{item.label}</span>}
          {index < items.length - 1 ? <span className="sc-muted">/</span> : null}
        </span>
      ))}
    </nav>
  );
}
