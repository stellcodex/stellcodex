import { Card } from "@/components/primitives/Card";

export interface PublicShareTerminalStateProps {
  title: string;
  description: string;
}

export function PublicShareTerminalState({ description, title }: PublicShareTerminalStateProps) {
  return (
    <main className="grid min-h-screen place-items-center bg-white px-4">
      <Card className="w-full max-w-[900px]" description={description} title={title}>
        <div className="text-sm text-[var(--foreground-muted)]">This link is no longer available.</div>
      </Card>
    </main>
  );
}
