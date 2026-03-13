import { ShareViewerClient } from "@/components/share/ShareViewerClient";

export default async function StandaloneSharePage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = await params;
  return <ShareViewerClient token={token} />;
}
