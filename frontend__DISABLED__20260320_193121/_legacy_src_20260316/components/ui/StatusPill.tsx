import { tokens } from "@/lib/tokens";

const variants: Record<string, { bg: string; text: string; border: string }> = {
  queued: { bg: "#f7f5ef", text: "#4f6f6b", border: tokens.border.color },
  running: { bg: "#eef6f5", text: tokens.accent.text, border: tokens.accent.soft },
  ready: { bg: "#e8f1ff", text: "#1d4ed8", border: "#c7ddff" },
  failed: { bg: "#fff1f2", text: "#b91c1c", border: "#fecdd3" },
};

export function StatusPill({
  status,
  label,
}: {
  status: "queued" | "running" | "ready" | "failed";
  label?: string;
}) {
  const v = variants[status];
  return (
    <span
      className="inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold"
      style={{
        background: v.bg,
        color: v.text,
        border: `1px solid ${v.border}`,
      }}
    >
      {label || status}
    </span>
  );
}
