import { FileWorkspace } from "@/components/product/FileWorkspace";

export default async function FileDetailPage({ params }: { params: Promise<{ fileId: string }> }) {
  const { fileId } = await params;
  return <FileWorkspace fileId={fileId} />;
}
