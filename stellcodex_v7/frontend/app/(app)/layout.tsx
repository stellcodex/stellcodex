import { TenantGuard } from "@/components/shell/TenantGuard";

export default function AppGroupLayout({ children }: { children: React.ReactNode }) {
  return <TenantGuard>{children}</TenantGuard>;
}
