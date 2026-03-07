import { AppModulePageClient } from "@/components/apps/AppModulePageClient";

export default async function AppModulePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  return <AppModulePageClient slug={slug} />;
}
