"use client";

import { useState } from "react";

export default function GlobalSearch() {
  const [query, setQuery] = useState("");

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter") {
      event.preventDefault();
      const trimmed = query.trim();
      if (!trimmed) {
        return;
      }
      window.dispatchEvent(new CustomEvent("chat-intent", { detail: { query: trimmed } }));
    }
  };

  return (
    <div className="px-6 pt-6">
      <div className="rounded-2xl border border-[#E5E7EB] bg-white px-4 py-3 shadow-sm">
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Herhangi bir şey sor"
          className="w-full bg-transparent text-base text-[#111827] outline-none placeholder:text-[#6B7280]"
        />
      </div>
    </div>
  );
}
