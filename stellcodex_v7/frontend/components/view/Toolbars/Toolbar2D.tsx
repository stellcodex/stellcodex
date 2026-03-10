export function Toolbar2D() {
  return (
    <div className="flex flex-wrap gap-2">
      <button className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm">Measure</button>
      <button className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm">Layers</button>
      <button className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm">Pan/Zoom</button>
    </div>
  );
}
