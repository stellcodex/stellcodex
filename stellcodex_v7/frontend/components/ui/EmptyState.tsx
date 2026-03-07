import { Card } from "@/components/ui/Card";
import { tokens } from "@/lib/tokens";

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <Card className="p-4">
      <div style={tokens.typography.h2} className="text-[#0c2a2a]">
        {title}
      </div>
      <div style={tokens.typography.body} className="mt-2 text-[#4f6f6b]">
        {description}
      </div>
      {action ? <div className="mt-4">{action}</div> : null}
    </Card>
  );
}
