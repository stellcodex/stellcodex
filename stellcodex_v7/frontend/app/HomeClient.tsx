"use client";

import Link from "next/link";
import { LayoutShell } from "@/components/layout/LayoutShell";
import { useScxContext, withScxContext } from "@/components/common/useScxContext";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { SecondaryButton } from "@/components/ui/SecondaryButton";
import { Card } from "@/components/ui/Card";
import { Container } from "@/components/ui/Container";
import { Section } from "@/components/ui/Section";
import { EmptyState } from "@/components/ui/EmptyState";
import { tokens } from "@/lib/tokens";
import { applications } from "@/data/applications";

export default function HomeClient() {
  const context = useScxContext();
  const cardHref = (path: string) => (context.project || context.scx ? withScxContext(path, context) : path);
  const recentFiles: { id: string; name: string; status: string }[] = [];

  return (
    <LayoutShell>
      <Container className="py-6 sm:py-8">
        <div className="flex flex-col gap-4">
          <Card>
            <div className="relative aspect-[16/9] overflow-hidden rounded-2xl">
              <div
                className="absolute inset-0"
                style={{
                  backgroundImage:
                    "linear-gradient(135deg, rgba(0,0,0,0.04), rgba(0,0,0,0.0)), repeating-linear-gradient(0deg, rgba(0,0,0,0.06) 0, rgba(0,0,0,0.06) 1px, transparent 1px, transparent 32px), repeating-linear-gradient(90deg, rgba(0,0,0,0.06) 0, rgba(0,0,0,0.06) 1px, transparent 1px, transparent 32px)",
                }}
              />
              <div className="relative z-10 flex h-full flex-col justify-between p-5 md:p-5">
                <div className="max-w-2xl space-y-3">
                  <div style={tokens.typography.h1} className="text-[#0c2a2a]">STELLCODEX</div>
                  <div style={tokens.typography.h2} className="text-[#0c2a2a]">
                    2D and 3D engineering workspace
                  </div>
                  <div style={tokens.typography.body} className="text-[#4f6f6b]">
                    Upload -> Review -> Inspect -> Render -> Share
                  </div>
                </div>
                <div>
                  <PrimaryButton href="/dashboard">Open dashboard</PrimaryButton>
                </div>
              </div>
            </div>
          </Card>

          <Section title="Modes">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              {applications.map((app) => (
                <Link key={app.key} href={cardHref(app.href)} className="block">
                  <Card hover className="p-4">
                    <div className="flex items-center gap-3">
                      <span className="text-xl">{app.icon}</span>
                      <div style={tokens.typography.h2} className="text-[#0c2a2a]">
                        {app.homeLabel ?? app.label}
                      </div>
                    </div>
                    <div style={tokens.typography.body} className="mt-2 text-[#4f6f6b]">
                      {app.description}
                    </div>
                  </Card>
                </Link>
              ))}
            </div>
          </Section>

          <Section title="Recent Files">
            {recentFiles.length ? (
              <div className="grid gap-3">
                {recentFiles.map((file) => (
                  <Card key={file.id} className="p-4">
                    <div style={tokens.typography.h2} className="text-[#0c2a2a]">
                      {file.name}
                    </div>
                    <div style={tokens.typography.body} className="mt-1 text-[#4f6f6b]">
                      {file.status}
                    </div>
                  </Card>
                ))}
              </div>
            ) : (
              <EmptyState
                title="No files yet"
                description="Start by uploading your first file."
                action={<SecondaryButton href="/dashboard">Open dashboard</SecondaryButton>}
              />
            )}
          </Section>
        </div>
      </Container>
    </LayoutShell>
  );
}
