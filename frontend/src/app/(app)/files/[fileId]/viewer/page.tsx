import { ViewerWorkspace } from "@/components/product/ViewerWorkspace";

export default async function ViewerPage({ params }: { params: Promise<{ fileId: string }> }) {
  const { fileId } = await params;
  return <ViewerWorkspace fileId={fileId} />;
}
