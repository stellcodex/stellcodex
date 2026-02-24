import Link from "next/link";
import { AppShell } from "@/components/layout/AppShell";
import { UploadDropzone } from "@/components/upload/UploadDropzone";

export default function HomePage() {
  return (
    <AppShell>
      <div className="grid min-h-[calc(100vh-3rem)] place-items-center">
        <div className="grid w-full max-w-3xl justify-items-center gap-4">
          <UploadDropzone />
          <Link href="/share" className="text-sm text-slate-600 hover:text-slate-900 hover:underline">
            Projelerine git
          </Link>
        </div>
      </div>
    </AppShell>
  );
}
