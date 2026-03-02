import React from 'react';
import ConsoleSidebar from '../../components/shell/ConsoleSidebar';
import AIPanel from '../../components/shell/AIPanel';

export default function ConsoleLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen w-screen bg-[#1a1a1a] text-gray-100 overflow-hidden">
      {/* Left Navigation */}
      <ConsoleSidebar />
      
      {/* Center Stage (Work Area) */}
      <main className="flex-1 flex flex-col relative overflow-hidden bg-black/20">
        {children}
      </main>
      
      {/* Right Intelligence Panel */}
      <AIPanel />
    </div>
  );
}
