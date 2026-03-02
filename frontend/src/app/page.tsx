import React from 'react';
import Link from 'next/link';

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-[#1a1a1a] text-gray-100 font-sans selection:bg-blue-500/30">
      {/* Navigation */}
      <nav className="flex items-center justify-between px-8 py-6 border-b border-gray-800 bg-[#1a1a1a]/80 backdrop-blur-md sticky top-0 z-50">
        <div className="text-2xl font-bold tracking-tighter">
          STELL<span className="text-blue-500">CODEX</span>
        </div>
        <div className="flex items-center gap-8">
          <Link href="/features" className="text-sm font-medium text-gray-400 hover:text-white transition-colors">Features</Link>
          <Link href="/pricing" className="text-sm font-medium text-gray-400 hover:text-white transition-colors">Pricing</Link>
          <Link href="/login" className="px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-bold rounded-lg transition-all shadow-lg shadow-blue-900/20">
            SIGN IN
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="max-w-6xl mx-auto px-8 py-24 text-center">
        <div className="inline-block px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-[10px] font-bold uppercase tracking-[0.2em] mb-6">
          v5.0 Engineering Intelligence
        </div>
        <h1 className="text-6xl md:text-7xl font-extrabold tracking-tight mb-8 bg-gradient-to-b from-white to-gray-500 bg-clip-text text-transparent leading-[1.1]">
          The Digital Nervous System <br /> for Production.
        </h1>
        <p className="text-xl text-gray-400 max-w-2xl mx-auto mb-12 leading-relaxed">
          Advanced 3D/2D CAD visualization, automated production planning, and secure engineering asset management in a single integrated console.
        </p>
        <div className="flex flex-wrap justify-center gap-4">
          <Link href="/register" className="px-8 py-4 bg-white text-black hover:bg-gray-200 text-base font-bold rounded-xl transition-all active:scale-95 shadow-xl">
            GET STARTED FREE
          </Link>
          <Link href="/console" className="px-8 py-4 bg-[#2d2d2d] border border-gray-700 text-white hover:bg-[#363636] text-base font-bold rounded-xl transition-all active:scale-95">
            LAUNCH CONSOLE
          </Link>
        </div>
      </section>

      {/* Product Pillars */}
      <section className="max-w-6xl mx-auto px-8 py-24 border-t border-gray-800">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {[
            { id: "01", name: "SOLID PRO", desc: "Native STEP/IGES streaming engine." },
            { id: "02", name: "RAPID PRO", desc: "STL/OBJ mesh repair & analysis." },
            { id: "03", name: "DRAFT PRO", desc: "Precision DXF/DWG 2D rendering." },
            { id: "04", name: "ARCHIVE PRO", desc: "Secure engineering documentation." }
          ].map((pillar) => (
            <div key={pillar.id} className="group p-6 bg-[#2d2d2d]/30 border border-gray-800 rounded-2xl hover:border-blue-500/50 transition-all">
              <div className="text-blue-500 font-mono text-xs mb-4">{pillar.id}</div>
              <h3 className="text-lg font-bold text-white mb-2 group-hover:text-blue-400 transition-colors">{pillar.name}</h3>
              <p className="text-gray-500 text-sm">{pillar.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 border-t border-gray-800 text-center text-gray-600 text-xs tracking-widest font-medium uppercase">
        &copy; 2026 STELLCODEX — ALL RIGHTS RESERVED
      </footer>
    </main>
  );
}
