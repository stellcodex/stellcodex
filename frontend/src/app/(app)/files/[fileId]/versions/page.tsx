import { FileVersionsScreen } from "@/components/files/FileVersionsScreen";

export default async function FileVersionsPage({ params }: { params: Promise<{ fileId: string }> }) {
  const { fileId } = await params;
  return <FileVersionsScreen fileId={fileId} />;
}
