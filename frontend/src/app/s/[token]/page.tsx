import { PublicSharePage } from "@/components/share/PublicSharePage";

export default async function ShareTokenPublicPage({ params }: { params: Promise<{ token: string }> }) {
  const { token } = await params;
  return <PublicSharePage token={token} />;
}

