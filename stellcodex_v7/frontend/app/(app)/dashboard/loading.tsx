import { LoadingState } from "@/components/ui/StateBlocks";

export default function Loading() {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5">
      <LoadingState lines={6} />
    </div>
  );
}
