import { AppShell } from "@/components/shell/AppShell";
import { HomeSurface } from "@/components/shell/Surfaces";

export default function HomePage() {
  return (
    <AppShell section="home">
      <HomeSurface />
    </AppShell>
  );
}
