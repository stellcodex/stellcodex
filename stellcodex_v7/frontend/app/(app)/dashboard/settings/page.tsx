"use client";

import { useEffect, useState } from "react";
import { SectionHeader } from "@/components/layout/SectionHeader";
import { ACCENT_OPTIONS, APPEARANCE_KEYS, THEME_OPTIONS, type AccentColor, type ThemeMode, applyAppearance } from "@/lib/appearance";

function persistAppearance(theme: ThemeMode, accent: AccentColor) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(APPEARANCE_KEYS.theme, theme);
  window.localStorage.setItem(APPEARANCE_KEYS.accent, accent);
  document.cookie = `scx_theme=${theme}; path=/; max-age=31536000; samesite=lax`;
  document.cookie = `scx_accent=${accent}; path=/; max-age=31536000; samesite=lax`;
  applyAppearance(theme, accent);
}

export default function DashboardSettingsPage() {
  const [theme, setTheme] = useState<ThemeMode>("dark");
  const [accent, setAccent] = useState<AccentColor>("cyan");
  const [profileName, setProfileName] = useState("");
  const [company, setCompany] = useState("");

  useEffect(() => {
    if (typeof window === "undefined") return;
    const storedTheme = (window.localStorage.getItem(APPEARANCE_KEYS.theme) || "dark") as ThemeMode;
    const storedAccent = (window.localStorage.getItem(APPEARANCE_KEYS.accent) || "cyan") as AccentColor;
    setTheme(storedTheme);
    setAccent(storedAccent);
    applyAppearance(storedTheme, storedAccent);
  }, []);

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Settings"
        description="Theme, profile, and security settings."
        crumbs={[{ label: "Dashboard", href: "/dashboard" }, { label: "Settings" }]}
      />

      <section className="rounded-2xl border border-slate-200 bg-white p-5">
        <div className="text-sm font-semibold text-slate-900">Appearance</div>
        <div className="mt-4 grid gap-4 lg:grid-cols-2">
          <div>
            <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Theme</div>
            <div className="flex flex-wrap gap-2">
              {THEME_OPTIONS.map((option) => (
                <button
                  key={option}
                  type="button"
                  onClick={() => {
                    setTheme(option);
                    persistAppearance(option, accent);
                  }}
                  className={`rounded-lg border px-3 py-1.5 text-xs font-semibold ${
                    theme === option ? "border-slate-900 bg-slate-900 text-white" : "border-slate-300 bg-white text-slate-700"
                  }`}
                >
                  {option}
                </button>
              ))}
            </div>
          </div>

          <div>
            <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Accent Color</div>
            <div className="flex flex-wrap gap-2">
              {ACCENT_OPTIONS.map((option) => (
                <button
                  key={option}
                  type="button"
                  onClick={() => {
                    setAccent(option);
                    persistAppearance(theme, option);
                  }}
                  className={`rounded-lg border px-3 py-1.5 text-xs font-semibold capitalize ${
                    accent === option ? "border-slate-900 bg-slate-900 text-white" : "border-slate-300 bg-white text-slate-700"
                  }`}
                >
                  {option}
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-5">
        <div className="text-sm font-semibold text-slate-900">Profile</div>
        <div className="mt-4 grid gap-3 lg:grid-cols-2">
          <label className="grid gap-1 text-xs text-slate-600">
            Name
            <input
              value={profileName}
              onChange={(e) => setProfileName(e.target.value)}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900"
              placeholder="Full name"
            />
          </label>
          <label className="grid gap-1 text-xs text-slate-600">
            Company
            <input
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900"
              placeholder="Company"
            />
          </label>
        </div>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-5">
        <div className="text-sm font-semibold text-slate-900">Security</div>
        <div className="mt-3 grid gap-2 text-sm text-slate-600">
          <div>Connected accounts: Google / Apple / Facebook</div>
          <div>Session handling: cookie-backed session is active for a single-session experience.</div>
        </div>
      </section>
    </div>
  );
}
