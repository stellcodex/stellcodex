import { redirect } from "next/navigation";

export default function LegacyDashboardFilesPage() {
  redirect("/files");
}
