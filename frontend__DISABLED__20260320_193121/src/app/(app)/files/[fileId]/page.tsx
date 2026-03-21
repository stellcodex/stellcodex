import { FileDetailScreen } from "@/components/files/FileDetailScreen";

export default async function FileDetailPage({ params }: { params: Promise<{ fileId: string }> }) {
  const { fileId } = await params;
  return <FileDetailScreen fileId={fileId} />;
}
