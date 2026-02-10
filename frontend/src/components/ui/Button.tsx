import Link from "next/link";
import React from "react";

type AProps = React.AnchorHTMLAttributes<HTMLAnchorElement> & { href: string };
type BProps = React.ButtonHTMLAttributes<HTMLButtonElement> & { href?: undefined };

export function Button(
  props: (AProps | BProps) & { variant?: "primary" | "secondary" | "ghost" }
) {
  const v = props.variant ?? "primary";
  const base =
    "inline-flex items-center justify-center rounded-xl px-4 py-2 text-sm font-medium transition " +
    "focus:outline-none focus:ring-2 focus:ring-[#2b7a76] focus:ring-offset-2 focus:ring-offset-[#f3f2ee]";
  const styles =
    v === "primary"
      ? "bg-[#0c3b3a] text-white hover:bg-[#0f4a47]"
      : v === "secondary"
      ? "bg-[#f7f5ef] text-[#0c2a2a] border border-[#d7d3c8] hover:bg-[#efede6]"
      : "bg-transparent text-[#1d5a57] hover:bg-[#e7efe9]";

  if ("href" in props && props.href) {
    const { href, className, variant, ...rest } = props as any;
    return (
      <Link href={href} className={[base, styles, className].filter(Boolean).join(" ")} {...rest} />
    );
  }

  const { className, variant, ...rest } = props as any;
  return <button className={[base, styles, className].filter(Boolean).join(" ")} {...rest} />;
}
