import Link from "next/link";
import { LayoutShell } from "@/components/layout/LayoutShell";
import { Card } from "@/components/ui/Card";
import { Container } from "@/components/ui/Container";
import { PageHeader } from "@/components/ui/PageHeader";
import { tokens } from "@/lib/tokens";
import { applications } from "@/data/applications";

export default function AppsPage() {
  return (
    <LayoutShell>
      <Container className="py-6 sm:py-8">
        <PageHeader title="Uygulamalar" subtitle="Uygulamalar" />
        <div className="mt-6 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {applications.map((app) => (
            <Link key={app.href} href={app.href} className="block">
              <Card hover className="p-4">
                <div className="flex items-center gap-3">
                  <span className="text-xl">{app.icon}</span>
                  <div style={tokens.typography.h2} className="text-[#0c2a2a]">
                    {app.label}
                  </div>
                </div>
                <div style={tokens.typography.body} className="mt-2 text-[#4f6f6b]">
                  {app.description}
                </div>
              </Card>
            </Link>
          ))}
        </div>
      </Container>
    </LayoutShell>
  );
}
