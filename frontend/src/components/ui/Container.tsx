import { tokens } from "@/lib/tokens";

export function Container({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`md:px-8 ${className ?? ""}`}
      style={{
        maxWidth: tokens.layout.containerMaxWidth,
        margin: "0 auto",
        paddingLeft: tokens.layout.pagePaddingX.base,
        paddingRight: tokens.layout.pagePaddingX.base,
      }}
    >
      {children}
    </div>
  );
}
