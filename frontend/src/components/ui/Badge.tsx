import React from "react";

export function Badge(props: { children: React.ReactNode; className?: string }) {
  return (
    <span
      className={[
        "inline-flex items-center rounded-full border border-slate-200 bg-white px-2.5 py-1 text-xs font-medium text-slate-700",
        props.className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {props.children}
    </span>
  );
}
