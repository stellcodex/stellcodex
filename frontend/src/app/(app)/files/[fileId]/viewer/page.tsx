import { ViewerScreen } from "@/components/viewer/ViewerScreen";

export default async function ViewerPage({ params }: { params: Promise<{ fileId: string }> }) {
  const { fileId } = await params;
  return <ViewerScreen fileId={fileId} />;
}
