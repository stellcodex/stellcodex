type ScxContextHeaderProps = {
  fileName?: string;
  format?: string;
  status?: string;
};

export function ScxContextHeader({ fileName, format, status }: ScxContextHeaderProps) {
  return (
    <div className="flex flex-col gap-sp1 rounded-r2 border-soft bg-surface px-cardPad py-cardPad">
      <div className="flex items-center justify-between">
        <div className="text-fs2 font-semibold">{fileName || "File"}</div>
        <div className="text-fs0 text-muted">{status || "Ready"}</div>
      </div>
      <div className="text-fs0 text-muted">{format || "GLB"}</div>
      <div className="flex items-center gap-sp1">
        <button className="h-btnH rounded-r1 border-soft bg-surface px-sp2 text-fs0">Fit</button>
        <button className="h-btnH rounded-r1 border-soft bg-surface px-sp2 text-fs0">Home View</button>
        <button className="h-btnH rounded-r1 border-soft bg-surface px-sp2 text-fs0">Share</button>
      </div>
    </div>
  );
}
