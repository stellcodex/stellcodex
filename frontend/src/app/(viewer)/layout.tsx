import { MasterFrame } from "@/components/layout/MasterFrame";
export const dynamic = "force-dynamic";

export default function ViewerLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <MasterFrame>{children}</MasterFrame>;
}
