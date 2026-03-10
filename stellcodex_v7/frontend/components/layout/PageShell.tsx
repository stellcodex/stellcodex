import React from "react";

export function PageShell(props: {
  title: string;
  subtitle?: string;
  children?: React.ReactNode;
  right?: React.ReactNode;
}) {
  return (
    <div className="p-4 sm:p-5">
      <div className="mx-auto max-w-6xl">
        <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-[#0c2a2a]">{props.title}</h1>
            {props.subtitle ? (
              <p className="mt-1 text-sm text-[#4f6f6b]">{props.subtitle}</p>
            ) : null}
          </div>
          {props.right ? <div className="flex items-center gap-2">{props.right}</div> : null}
        </div>

        <div className="rounded-2xl border border-[#d7d3c8] bg-white/90 p-5 shadow-sm">
          {props.children ?? <div className="text-sm text-[#4f6f6b]">Content is ready.</div>}
        </div>
      </div>
    </div>
  );
}
