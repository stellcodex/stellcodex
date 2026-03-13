import { redirect } from "next/navigation";

export default async function LegacyViewerPage({
  params,
}: {
  params: Promise<{ file_id: string }>;
}) {
  const { file_id } = await params;
  redirect(`/view/${file_id}`);
}
