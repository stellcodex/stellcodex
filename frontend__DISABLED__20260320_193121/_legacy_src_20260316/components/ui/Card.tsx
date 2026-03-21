import { tokens } from "@/lib/tokens";

export function Card({
  children,
  className,
  hover,
}: {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
}) {
  return (
    <div
      className={className}
      style={{
        borderRadius: tokens.radii.md,
        border: `${tokens.border.width} solid ${tokens.border.color}`,
        boxShadow: tokens.shadow.sm,
        background: "#fff",
        transition: "transform 150ms ease, box-shadow 150ms ease",
        ...(hover
          ? {
              cursor: "pointer",
            }
          : null),
      }}
    >
      {children}
    </div>
  );
}
