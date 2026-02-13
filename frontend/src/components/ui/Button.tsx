import Link from "next/link";
import React from "react";

type AProps = React.AnchorHTMLAttributes<HTMLAnchorElement> & { href: string };
type BProps = React.ButtonHTMLAttributes<HTMLButtonElement> & { href?: undefined };

export function Button(
  props: (AProps | BProps) & { variant?: "primary" | "secondary" | "ghost" }
) {
  const v = props.variant ?? "primary";
  const base =
    "inline-flex h-10 items-center justify-center rounded-xl px-4 text-sm font-medium transition " +
    "focus:outline-none focus:ring-2 focus:ring-[#9ca3af] focus:ring-offset-2 focus:ring-offset-[#f7f7f8]";
  const styles =
    v === "primary"
      ? "border border-[#d1d5db] bg-[#111827] text-white hover:bg-[#1f2937]"
      : v === "secondary"
      ? "border border-[#d1d5db] bg-white text-[#111827] hover:bg-[#f3f4f6]"
      : "bg-transparent text-[#374151] hover:bg-[#f3f4f6]";

  if ("href" in props && props.href) {
    const { href, className, variant, ...rest } = props as any;
    return (
      <Link href={href} className={[base, styles, className].filter(Boolean).join(" ")} {...rest} />
    );
  }

  const { className, variant, ...rest } = props as any;
  return <button className={[base, styles, className].filter(Boolean).join(" ")} {...rest} />;
}
