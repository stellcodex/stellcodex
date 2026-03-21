import { Card } from "@/components/primitives/Card";

export interface PublicShareTerminalStateProps {
  title: string;
  description: string;
}

export function PublicShareTerminalState({ description, title }: PublicShareTerminalStateProps) {
  return (
    <main className="grid min-h-screen place-items-center px-6">
      <Card className="w-full max-w-xl" description={description} title={title}>
        <div className="text-sm text-[var(--foreground-muted)]">The public share route is terminal and intentionally exposes no internal application chrome.</div>
      </Card>
    </main>
  );
}
