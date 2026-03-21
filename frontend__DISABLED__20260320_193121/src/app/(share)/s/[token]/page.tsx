import { PublicShareScreen } from "@/components/shares/PublicShareScreen";

export default async function PublicSharePage({ params }: { params: Promise<{ token: string }> }) {
  const { token } = await params;
  return <PublicShareScreen token={token} />;
}
