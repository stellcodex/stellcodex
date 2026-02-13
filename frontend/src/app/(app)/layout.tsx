import { MasterFrame } from "@/components/layout/MasterFrame";

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <MasterFrame mainClassName="min-h-[calc(100vh-200px)]">{children}</MasterFrame>;
}
