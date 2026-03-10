import Image from "next/image";
import Link from "next/link";
import { Button } from "@/components/ui/Button";

export default function HomePage() {
  return (
    <main className="mx-auto max-w-6xl px-6 py-6 sm:py-8">
      <section className="grid gap-4 lg:grid-cols-[1.15fr_0.85fr]">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full border border-[#d7d3c8] bg-[#f7f5ef] px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-[#4f6f6b]">
            STELLCODEX ENGINEERING WORKSPACE
          </div>
          <h1 className="mt-4 text-xl font-semibold tracking-tight text-[#0c2a2a] sm:text-2xl">
            Review. Inspect. Share. Engineering data without CAD installs.
          </h1>
          <p className="mt-4 max-w-xl text-sm text-[#2c4b49]">
            Built for industrial designers, manufacturing teams, and decision makers without CAD licenses.
            Upload a file, view it in 2D or 3D, and share it with a controlled link.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Button href="/dashboard">Dashboard</Button>
            <Button href="/docs" variant="ghost">
              Docs
            </Button>
          </div>

          <div className="mt-8 grid gap-3 sm:grid-cols-3">
            <div className="rounded-2xl border border-[#d7d3c8] bg-[#f7f5ef] px-4 py-3 text-xs text-[#4f6f6b]">
              Read-only review
            </div>
            <div className="rounded-2xl border border-[#d7d3c8] bg-[#f7f5ef] px-4 py-3 text-xs text-[#4f6f6b]">
              Server-side conversion
            </div>
            <div className="rounded-2xl border border-[#d7d3c8] bg-[#f7f5ef] px-4 py-3 text-xs text-[#4f6f6b]">
              Secure sharing links
            </div>
          </div>
        </div>

        <div className="relative">
          <div className="rounded-3xl border border-[#d7d3c8] bg-[#f7f5ef] p-5 shadow-sm">
            <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-[0.2em] text-[#4f6f6b]">
              <span>Viewer Preview</span>
              <span className="rounded-full border border-[#d7d3c8] bg-white px-2 py-1 text-[10px]">
                Read-only
              </span>
            </div>
            <div className="mt-4 overflow-hidden rounded-2xl border border-[#e3dfd3] bg-white">
              <Image
                src="/preview.svg"
                alt="Stellcodex viewer preview"
                width={900}
                height={560}
                className="h-auto w-full"
                priority
              />
            </div>
            <div className="mt-4 grid grid-cols-3 gap-2 text-xs text-[#4f6f6b]">
              <div className="rounded-xl border border-[#e3dfd3] bg-white px-3 py-2 text-center">
                Orbit
              </div>
              <div className="rounded-xl border border-[#e3dfd3] bg-white px-3 py-2 text-center">
                Measure
              </div>
              <div className="rounded-xl border border-[#e3dfd3] bg-white px-3 py-2 text-center">
                Share
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="mt-10 grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="rounded-3xl border border-[#d7d3c8] bg-white/70 p-5 shadow-sm">
          <div className="text-sm font-semibold text-[#0c2a2a]">Workflow at a glance</div>
          <div className="mt-4 grid gap-3 text-sm text-[#2c4b49] sm:grid-cols-4">
            <div className="rounded-2xl border border-[#e3dfd3] bg-[#f7f5ef] px-3 py-3 text-center">
              Upload
            </div>
            <div className="rounded-2xl border border-[#e3dfd3] bg-[#f7f5ef] px-3 py-3 text-center">
              Convert
            </div>
            <div className="rounded-2xl border border-[#e3dfd3] bg-[#f7f5ef] px-3 py-3 text-center">
              View
            </div>
            <div className="rounded-2xl border border-[#e3dfd3] bg-[#f7f5ef] px-3 py-3 text-center">
              Share
            </div>
          </div>
        </div>

        <div className="rounded-3xl border border-[#d7d3c8] bg-[#0c3b3a] p-5 text-white shadow-sm">
          <div className="text-sm font-semibold">Before you upload</div>
          <p className="mt-2 text-sm text-white/80">
            STEP, IGES, STL, PDF, PNG, DXF, and more. Upload and viewing stay smooth,
            stable, and secure.
          </p>
          <div className="mt-4">
            <Button href="/dashboard" variant="secondary">
              Open dashboard
            </Button>
          </div>
        </div>
      </section>

      <section className="mt-10">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.2em] text-[#4f6f6b]">
              Why STELLCODEX
            </div>
            <h2 className="mt-3 text-xl font-semibold text-[#0c2a2a] sm:text-2xl">
              Move technical decisions faster without a CAD seat.
            </h2>
          </div>
          <Link className="text-sm font-semibold text-[#1d5a57] hover:text-[#0c2a2a]" href="/docs">
            Help center ->
          </Link>
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-2">
          <div className="rounded-3xl border border-[#d7d3c8] bg-white/80 p-5 shadow-sm">
            <div className="text-sm font-semibold text-[#0c2a2a]">2D + 3D in one place</div>
            <p className="mt-2 text-sm text-[#2c4b49]">
              One link keeps engineering teams and customers aligned on the same model.
            </p>
          </div>
          <div className="rounded-3xl border border-[#d7d3c8] bg-white/80 p-5 shadow-sm">
            <div className="text-sm font-semibold text-[#0c2a2a]">Secure sharing</div>
            <p className="mt-2 text-sm text-[#2c4b49]">
              Read-only review with version control and controlled sharing limits.
            </p>
          </div>
          <div className="rounded-3xl border border-[#d7d3c8] bg-white/80 p-5 shadow-sm">
            <div className="text-sm font-semibold text-[#0c2a2a]">Server-side conversion</div>
            <p className="mt-2 text-sm text-[#2c4b49]">
              No local setup. Conversion and previews run from a single controlled backend.
            </p>
          </div>
          <div className="rounded-3xl border border-[#d7d3c8] bg-white/80 p-5 shadow-sm">
            <div className="text-sm font-semibold text-[#0c2a2a]">Built for teams</div>
            <p className="mt-2 text-sm text-[#2c4b49]">
              File states, viewing links, and a central control surface stay connected.
            </p>
          </div>
        </div>
      </section>

      <section className="mt-10 grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="rounded-3xl border border-[#d7d3c8] bg-[#f7f5ef] p-5 shadow-sm">
          <div className="text-sm font-semibold text-[#0c2a2a]">Who it is for</div>
          <ul className="mt-3 grid gap-2 text-sm text-[#2c4b49]">
            <li>Industrial design and product teams</li>
            <li>Manufacturing and technical sourcing teams</li>
            <li>Managers and suppliers without CAD licenses</li>
            <li>Quality and technical review teams</li>
          </ul>
        </div>

        <div className="rounded-3xl border border-[#d7d3c8] bg-white/80 p-5 shadow-sm">
          <div className="text-sm font-semibold text-[#0c2a2a]">Community</div>
          <p className="mt-2 text-sm text-[#2c4b49]">
            Curated model libraries, example files, and community shares.
          </p>
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            {Array.from({ length: 3 }).map((_, idx) => (
              <div
                key={idx}
                className="rounded-2xl border border-dashed border-[#d7d3c8] bg-[#f7f5ef] px-3 py-6 text-center text-xs text-[#4f6f6b]"
              >
                Preview
              </div>
            ))}
          </div>
          <div className="mt-4">
            <Button href="/docs" variant="secondary">
              Docs
            </Button>
          </div>
        </div>
      </section>

      <section className="mt-10 grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="rounded-3xl border border-[#d7d3c8] bg-white/80 p-5 shadow-sm">
          <div className="text-sm font-semibold text-[#0c2a2a]">Documentation</div>
          <p className="mt-2 text-sm text-[#2c4b49]">
            Quick guides, format lists, and troubleshooting paths in one place.
          </p>
          <div className="mt-4 flex flex-wrap gap-2 text-xs">
            <span className="rounded-full border border-[#d7d3c8] bg-[#f7f5ef] px-3 py-1">Getting Started</span>
            <span className="rounded-full border border-[#d7d3c8] bg-[#f7f5ef] px-3 py-1">Formats</span>
            <span className="rounded-full border border-[#d7d3c8] bg-[#f7f5ef] px-3 py-1">Troubleshooting</span>
            <span className="rounded-full border border-[#d7d3c8] bg-[#f7f5ef] px-3 py-1">FAQ</span>
          </div>
        </div>

        <div className="rounded-3xl border border-[#d7d3c8] bg-[#0c3b3a] p-5 text-white shadow-sm">
          <div className="text-sm font-semibold">Security and limits</div>
          <ul className="mt-3 grid gap-2 text-sm text-white/80">
            <li>Read-only viewing</li>
            <li>Controlled sharing links</li>
            <li>PII masking and audit logging</li>
            <li>KVKK / GDPR aligned infrastructure</li>
          </ul>
        </div>
      </section>

      <section className="mt-10 rounded-3xl border border-[#d7d3c8] bg-[#f7f5ef] p-5 text-center shadow-sm">
        <h3 className="text-xl font-semibold text-[#0c2a2a] sm:text-2xl">
          Upload a file and review it immediately.
        </h3>
        <p className="mt-2 text-sm text-[#2c4b49]">
          Stellcodex is not a marketing shell. It is the product itself.
        </p>
        <div className="mt-5 flex flex-wrap justify-center gap-3">
          <Button href="/dashboard">Open dashboard</Button>
          <Button href="/login" variant="secondary">
            Sign in
          </Button>
        </div>
      </section>
    </main>
  );
}
