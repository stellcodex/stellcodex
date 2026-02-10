import React from "react";

export function PageShell(props: {
  title: string;
  subtitle?: string;
  children?: React.ReactNode;
  right?: React.ReactNode;
}) {
  return (
    <div className="p-4 sm:p-6">
      <div className="mx-auto max-w-6xl">
        <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">{props.title}</h1>
            {props.subtitle ? (
              <p className="mt-1 text-sm text-slate-600">{props.subtitle}</p>
            ) : null}
          </div>
          {props.right ? <div className="flex items-center gap-2">{props.right}</div> : null}
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          {props.children ?? <div className="text-sm text-slate-600">Content ready.</div>}
        </div>
      </div>
    </div>
  );
}
