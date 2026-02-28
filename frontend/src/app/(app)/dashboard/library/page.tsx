import Link from "next/link";
import { SectionHeader } from "@/components/layout/SectionHeader";

export default function DashboardLibraryPage() {
  return (
    <div className="space-y-6">
      <SectionHeader
        title="Library"
        description="Yayınlanan modeller, unlisted paylaşımlar ve görünürlük yönetimi."
        crumbs={[{ label: "Panel", href: "/dashboard" }, { label: "Library" }]}
      />

      <div className="rounded-2xl border border-slate-200 bg-white p-5">
        <div className="flex items-center justify-between gap-3">
          <div className="text-sm font-semibold text-slate-900">Publish Queue</div>
          <Link href="/library" className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700">
            Public Feed
          </Link>
        </div>
        <div className="mt-3 grid gap-3 text-sm text-slate-600">
          <div className="rounded-xl border border-slate-100 bg-slate-50 px-3 py-2">Visibility: Private / Unlisted / Public</div>
          <div className="rounded-xl border border-slate-100 bg-slate-50 px-3 py-2">Publish flow: Explorer üzerinden tek tık yayınla</div>
        </div>
      </div>
    </div>
  );
}

