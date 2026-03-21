import { Button } from "@/components/ui/Button";

export default function HomePage() {
  const startApps = [
    { name: "3D Review", href: "/app/viewer3d", caption: "STEP, STL, OBJ, GLB" },
    { name: "2D Drawings", href: "/app/viewer2d", caption: "DXF and flat drawings" },
    { name: "Documents", href: "/app/docviewer", caption: "PDF, images, Office" },
    { name: "Files & Share", href: "/files", caption: "Uploads, status, share" },
    { name: "Projects", href: "/projects", caption: "Project containers" },
    { name: "Applications", href: "/apps", caption: "All app surfaces" },
  ] as const;
  const routingRules = [
    { label: "3D", formats: "STEP, STL, OBJ, GLB", target: "Viewer 3D" },
    { label: "2D", formats: "DXF, flat technical files", target: "Viewer 2D" },
    { label: "DOC", formats: "PDF, Office, images", target: "Documents" },
  ] as const;

  return (
    <main className="mx-auto max-w-6xl px-6 py-8">
      <section className="rounded-[32px] border border-[#e5e7eb] bg-white p-6 shadow-[0_16px_42px_rgba(15,23,42,0.04)] sm:p-8">
        <div className="max-w-3xl">
          <div className="inline-flex items-center rounded-full border border-[#e5e7eb] bg-[#fcfcfb] px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-[#6b7280]">
            STELLCODEX
          </div>
          <h1 className="mt-4 text-3xl font-semibold tracking-[-0.04em] text-[#111827] sm:text-5xl">
            One file in. The right app opens.
          </h1>
          <div className="mt-6 flex flex-wrap gap-3">
            <Button href="/">Open workspace</Button>
            <Button href="/upload" variant="secondary">
              Upload file
            </Button>
            <Button href="/apps" variant="ghost">
              Applications
            </Button>
          </div>
        </div>

        <div className="mt-8 grid gap-3 md:grid-cols-3">
          {routingRules.map((rule) => (
            <div key={rule.label} className="rounded-[22px] border border-[#e5e7eb] bg-[#fcfcfb] p-4">
              <div className="flex items-center justify-between gap-3">
                <div className="text-sm font-semibold text-[#111827]">{rule.label}</div>
                <span className="rounded-full border border-[#e5e7eb] px-2.5 py-1 text-[11px] text-[#6b7280]">{rule.target}</span>
              </div>
              <div className="mt-3 text-sm text-[#4b5563]">{rule.formats}</div>
            </div>
          ))}
        </div>
      </section>

      <section className="mt-6 grid gap-4 lg:grid-cols-[340px_minmax(0,1fr)]">
        <div className="rounded-[28px] border border-[#e5e7eb] bg-[#fcfcfb] p-5 shadow-[0_12px_30px_rgba(15,23,42,0.04)]">
          <div className="text-xs font-semibold uppercase tracking-[0.2em] text-[#6b7280]">Start points</div>
          <div className="mt-4 space-y-2">
            <Button href="/upload" variant="secondary" className="w-full justify-start">
              Upload a file
            </Button>
            <Button href="/files" variant="secondary" className="w-full justify-start">
              Files & Share
            </Button>
            <Button href="/projects" variant="secondary" className="w-full justify-start">
              Projects
            </Button>
            <Button href="/apps" variant="secondary" className="w-full justify-start">
              Applications
            </Button>
          </div>
        </div>

        <div className="rounded-[28px] border border-[#e5e7eb] bg-white p-5 shadow-[0_12px_30px_rgba(15,23,42,0.04)]">
          <div className="text-xs font-semibold uppercase tracking-[0.2em] text-[#6b7280]">Core apps</div>
          <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {startApps.map((app) => (
              <a
                key={app.name}
                href={app.href}
                className="rounded-[22px] border border-[#e5e7eb] bg-[#fcfcfb] p-4 transition hover:border-[#cfd8d8] hover:bg-[#f8fbfb]"
              >
                <div className="text-sm font-semibold text-[#111827]">{app.name}</div>
                <div className="mt-2 text-sm text-[#4b5563]">{app.caption}</div>
              </a>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
