"use client";

import { useSearchParams } from "next/navigation";

export type ScxContext = {
  project: string | null;
  scx: string | null;
};

export function useScxContext(): ScxContext {
  const params = useSearchParams();
  return {
    project: params.get("project"),
    scx: params.get("scx"),
  };
}

export function withScxContext(path: string, context: ScxContext): string {
  const query = new URLSearchParams();
  if (context.project) query.set("project", context.project);
  if (context.scx) query.set("scx", context.scx);
  const qs = query.toString();
  return qs ? `${path}?${qs}` : path;
}
