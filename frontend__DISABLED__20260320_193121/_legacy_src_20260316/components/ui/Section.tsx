import { tokens } from "@/lib/tokens";

export function Section({
  title,
  description,
  children,
  className,
}: {
  title?: string;
  description?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section className={className} style={{ marginTop: tokens.spacing.lg }}>
      {title ? (
        <div className="mb-3">
          <div style={tokens.typography.h2} className="text-[#0c2a2a]">
            {title}
          </div>
          {description ? (
            <div style={tokens.typography.body} className="mt-1 text-[#4f6f6b]">
              {description}
            </div>
          ) : null}
        </div>
      ) : null}
      {children}
    </section>
  );
}
