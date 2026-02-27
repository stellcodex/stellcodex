import { MasterFrame } from "@/components/layout/MasterFrame";
export const dynamic = "force-dynamic";

export default function ViewerLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <MasterFrame showFooter={false} mainClassName="h-[calc(100dvh-4rem)] overflow-hidden">{children}</MasterFrame>;
}
