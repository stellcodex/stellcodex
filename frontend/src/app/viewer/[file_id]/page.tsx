import { PlatformClient } from "@/components/platform/PlatformClient";

export default async function ViewerPage({
  params,
}: {
  params: Promise<{ file_id: string }>;
}) {
  const { file_id } = await params;
  return <PlatformClient view="viewer" fileId={file_id} />;
}
