export function AppFooter() {
  return (
    <footer className="border-t border-slate-200 bg-white">
      <div className="mx-auto max-w-6xl px-4 py-8">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div className="text-xs text-slate-500">
            STELLCODEX 3D VIEWER PRO • Modular • Commercial-grade • 2D/3D CAD/CAM
          </div>
          <div className="text-xs text-slate-500">
            © {new Date().getFullYear()} STELLCODEX
          </div>
        </div>
      </div>
    </footer>
  );
}
