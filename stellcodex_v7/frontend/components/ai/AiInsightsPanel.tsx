"use client";

import { useUser } from "@/context/UserContext";

type AiInsightsPanelProps = {
  mode: "admin" | "user";
};

const adminInsights = [
  "Render queue failures are increasing",
  "Blender jobs are slower than the recent average",
  "Layer extraction is delayed on DXF imports",
  "A backlog was detected in storage synchronization",
];

const userInsights = [
  "Try Render for the latest revisions",
  "Open 2D mode for DXF layer inspection",
  "Use Exploded View for assembly review",
];

export function AiInsightsPanel({ mode }: AiInsightsPanelProps) {
  const { user } = useUser();
  const items = mode === "admin" ? adminInsights : userInsights;

  return (
    <div className="flex flex-col gap-sp2 rounded-r2 border-soft bg-surface px-cardPad py-cardPad">
      <div className="text-fs1 font-semibold">AI Insights</div>
      <div className="text-fs0 text-muted">
        {mode === "admin" ? "Operational signals" : `For ${user.name}`}
      </div>
      <ul className="flex flex-col gap-sp1 text-fs1 text-text">
        {items.map((item) => (
          <li key={item} className="flex items-start gap-sp1">
            <span className="text-icon">•</span>
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
