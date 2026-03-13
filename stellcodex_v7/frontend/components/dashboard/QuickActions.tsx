import Link from "next/link";
import { Panel } from "@/components/primitives/Panel";
import { Button } from "@/components/primitives/Button";

export interface QuickActionsProps {
  onUploadClick: () => void;
}

export function QuickActions({ onUploadClick }: QuickActionsProps) {
  return (
    <Panel title="Quick actions">
      <div className="sc-inline">
        <Button variant="primary" onClick={onUploadClick}>
          Upload file
        </Button>
        <Link href="/projects" className="sc-button" data-variant="ghost">
          Open projects
        </Link>
        <Link href="/shares" className="sc-button" data-variant="ghost">
          Manage shares
        </Link>
      </div>
    </Panel>
  );
}
