import { redirect } from "next/navigation";

export default async function ViewerPage({
  params,
}: {
  params: Promise<{ file_id: string }>;
}) {
  const { file_id } = await params;
  redirect(`/view/${encodeURIComponent(file_id)}`);
}
