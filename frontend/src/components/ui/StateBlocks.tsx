import React from "react";

export function EmptyState(props: {
  title: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-6 text-center">
      <div className="text-sm font-semibold text-slate-900">{props.title}</div>
      {props.description ? (
        <p className="mt-2 text-sm text-slate-600">{props.description}</p>
      ) : null}
      {props.action ? <div className="mt-4 flex justify-center">{props.action}</div> : null}
    </div>
  );
}

export function ErrorState(props: {
  title: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-center">
      <div className="text-sm font-semibold text-red-700">{props.title}</div>
      {props.description ? (
        <p className="mt-2 text-sm text-red-600">{props.description}</p>
      ) : null}
      {props.action ? <div className="mt-4 flex justify-center">{props.action}</div> : null}
    </div>
  );
}

export function LoadingState({ lines = 3 }: { lines?: number }) {
  return (
    <div className="animate-pulse space-y-3">
      {Array.from({ length: lines }).map((_, idx) => (
        <div
          key={idx}
          className="h-3 rounded-full bg-slate-200"
          style={{ width: `${80 - idx * 10}%` }}
        />
      ))}
    </div>
  );
}
