import type { JobStage } from "@/lib/stellcodex/types";

const STAGES: Array<{ key: JobStage; label: string }> = [
  { key: "uploaded", label: "Uploaded" },
  { key: "security", label: "Security check" },
  { key: "preview", label: "Preparing preview" },
  { key: "ready", label: "Ready" },
];

export function ProcessingScreen({
  stage,
  progress,
  title = "Preparing",
  subtitle = "The file is processing in the background. The viewer will not open before it is ready.",
}: {
  stage: JobStage;
  progress: number;
  title?: string;
  subtitle?: string;
}) {
  const activeIndex = STAGES.findIndex((s) => s.key === stage);
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
      <p className="mt-1 text-sm text-slate-600">{subtitle}</p>

      <div className="mt-5 h-2 overflow-hidden rounded-full bg-slate-100">
        <div
          className="h-full rounded-full bg-slate-900 transition-all"
          style={{ width: `${Math.max(0, Math.min(progress, 100))}%` }}
        />
      </div>
      <div className="mt-2 text-xs text-slate-500">%{Math.round(progress)}</div>

      <ol className="mt-5 grid gap-3">
        {STAGES.map((item, idx) => {
          const done = idx < activeIndex || stage === "ready";
          const current = idx === activeIndex;
          return (
            <li key={item.key} className="flex items-center gap-3">
              <span
                className={[
                  "grid h-7 w-7 place-items-center rounded-full border text-xs font-semibold",
                  done
                    ? "border-slate-900 bg-slate-900 text-white"
                    : current
                      ? "border-slate-300 bg-slate-100 text-slate-700"
                      : "border-slate-200 bg-white text-slate-400",
                ].join(" ")}
              >
                {done ? "✓" : idx + 1}
              </span>
              <span className={current || done ? "text-slate-900" : "text-slate-500"}>{item.label}</span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
