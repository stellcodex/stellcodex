import { FileDetailScreen } from "@/components/files/FileDetailScreen";

export interface FileWorkspaceProps {
  fileId: string;
}

export function FileWorkspace({ fileId }: FileWorkspaceProps) {
  return <FileDetailScreen fileId={fileId} />;
}
