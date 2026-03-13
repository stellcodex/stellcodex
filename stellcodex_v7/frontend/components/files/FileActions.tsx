import Link from "next/link";
import type { FileSummary } from "@/lib/contracts/files";
import { Button } from "@/components/primitives/Button";

export interface FileActionsProps {
  file: FileSummary;
}

export function FileActions({ file }: FileActionsProps) {
  return (
    <div className="sc-inline">
      <Link href={`/files/${file.fileId}/viewer`} className="sc-button" data-variant="primary" aria-disabled={!file.viewerReady}>
        Open viewer
      </Link>
      <Button variant="ghost" disabled>
        New version
      </Button>
      <Link href="/shares" className="sc-button" data-variant="ghost">
        Shares
      </Link>
    </div>
  );
}
