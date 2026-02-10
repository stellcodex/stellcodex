import { SectionHeader } from "@/components/layout/SectionHeader";
import { EmptyState } from "@/components/ui/StateBlocks";

export default function DashboardActivityPage() {
  return (
    <div className="space-y-6">
      <SectionHeader
        title="Activity"
        description="Timeline of uploads, conversions, shares, and viewer actions."
        crumbs={[
          { label: "Dashboard", href: "/dashboard" },
          { label: "Activity" },
        ]}
      />

      <div className="rounded-2xl border border-slate-200 bg-white p-5">
        <div className="text-sm font-semibold text-slate-900">Filters</div>
        <p className="mt-2 text-sm text-slate-600">
          Event type, date range, file name.
        </p>
      </div>

      <EmptyState
        title="Henüz bir işlem yok"
        description="Activity events will appear here once data sources are wired."
      />
    </div>
  );
}
