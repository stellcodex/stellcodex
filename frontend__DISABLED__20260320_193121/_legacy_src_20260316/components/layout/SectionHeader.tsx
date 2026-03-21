import Link from "next/link";
import React from "react";

export type Breadcrumb = { label: string; href?: string };

export function SectionHeader(props: {
  title: string;
  description?: string;
  crumbs?: Breadcrumb[];
  actions?: React.ReactNode;
}) {
  const crumbs = props.crumbs ?? [];
  return (
    <div className="mb-6">
      {crumbs.length ? (
        <nav className="text-xs text-slate-500">
          <ol className="flex flex-wrap items-center gap-1">
            {crumbs.map((crumb, idx) => (
              <li key={`${crumb.label}-${idx}`} className="flex items-center gap-1">
                {crumb.href ? (
                  <Link href={crumb.href} className="hover:text-slate-700">
                    {crumb.label}
                  </Link>
                ) : (
                  <span className="text-slate-500">{crumb.label}</span>
                )}
                {idx < crumbs.length - 1 ? <span>/</span> : null}
              </li>
            ))}
          </ol>
        </nav>
      ) : null}
      <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900">{props.title}</h1>
          {props.description ? (
            <p className="mt-1 text-sm text-slate-600">{props.description}</p>
          ) : null}
        </div>
        {props.actions ? <div className="flex items-center gap-2">{props.actions}</div> : null}
      </div>
    </div>
  );
}
