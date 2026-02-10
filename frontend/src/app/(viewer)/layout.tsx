export const dynamic = "force-dynamic";

export default function ViewerLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <div className="min-h-screen bg-[#f3f2ee]">{children}</div>;
}
