import { tokens } from "@/lib/tokens";

export function PageHeader({
  title,
  subtitle,
  actions,
}: {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-4">
      <div>
        <div style={tokens.typography.label} className="uppercase tracking-[0.2em] text-[#4f6f6b]">
          {title}
        </div>
        {subtitle ? (
          <div
            style={{ ...tokens.typography.body, fontSize: tokens.typography.h2.fontSize, fontWeight: 600 }}
            className="mt-2 text-[#0c2a2a]"
          >
            {subtitle}
          </div>
        ) : null}
      </div>
      {actions ? <div className="flex items-center gap-2">{actions}</div> : null}
    </div>
  );
}
