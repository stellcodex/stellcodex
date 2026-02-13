"use client";

import { useShellUi } from "@/components/shell/AppShell";

type SelectOption = {
  label: string;
  value: string;
};

export function PageHeader({
  title,
  searchPlaceholder,
  primaryAction,
  filters,
}: {
  title: string;
  searchPlaceholder: string;
  primaryAction?: string;
  filters?: Array<{ label: string; options: SelectOption[] }>;
}) {
  const { canFocus, focusMode, toggleFocusMode } = useShellUi();

  return (
    <div className="mb-3 rounded-2xl border border-[#e2e8f0] bg-white p-3 shadow-[0_1px_2px_rgba(16,24,40,0.04)]">
      <div className="grid gap-2.5 xl:grid-cols-[minmax(170px,220px)_minmax(280px,1fr)_auto] xl:items-center">
        <h1 className="min-w-0 text-2xl font-semibold tracking-[-0.01em] text-[#0f172a]">{title}</h1>

        <input
          type="search"
          placeholder={searchPlaceholder}
          className="h-11 w-full rounded-xl border border-[#d0d7e2] bg-white px-3 text-sm text-[#0f172a] outline-none ring-0 placeholder:text-[#94a3b8] focus:border-[#7aa2e3]"
        />

        <div className="flex flex-wrap items-center gap-2 xl:justify-end">
          {(filters ?? []).map((filter) => (
            <label key={filter.label} className="inline-flex items-center gap-2 text-sm text-[#334155]">
              <span className="whitespace-nowrap">{filter.label}</span>
              <select className="h-11 rounded-xl border border-[#d0d7e2] bg-white px-3 text-sm text-[#0f172a] outline-none focus:border-[#7aa2e3]">
                {filter.options.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
          ))}

          {canFocus ? (
            <button
              type="button"
              className="inline-flex h-11 w-11 items-center justify-center rounded-xl border border-[#cfd8e3] bg-white text-[#1f2937] hover:bg-[#f8fafc]"
              onClick={toggleFocusMode}
              title={focusMode ? "Odaktan çık" : "Odak modu"}
              aria-label={focusMode ? "Odaktan çık" : "Odak modu"}
            >
              {focusMode ? (
                <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" aria-hidden>
                  <path d="M8 3H3v5M16 3h5v5M3 16v5h5M21 16v5h-5" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" />
                </svg>
              ) : (
                <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" aria-hidden>
                  <path d="M8 3H3v5M16 3h5v5M3 16v5h5M21 16v5h-5" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" />
                  <path d="M8 8L3 3M16 8l5-5M8 16l-5 5M16 16l5 5" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" />
                </svg>
              )}
            </button>
          ) : null}

          {primaryAction ? (
            <button
              type="button"
              className="inline-flex h-11 items-center justify-center rounded-xl border border-[#1d4ed8] bg-[#2563eb] px-4 text-sm font-semibold text-white hover:bg-[#1d4ed8]"
            >
              {primaryAction}
            </button>
          ) : null}
        </div>
      </div>
    </div>
  );
}
