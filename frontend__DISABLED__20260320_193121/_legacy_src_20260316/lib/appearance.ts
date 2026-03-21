export type ThemeMode = "system" | "dark" | "light";
export type AccentColor = "slate" | "cyan" | "emerald" | "amber" | "rose" | "indigo";

export const THEME_OPTIONS: ThemeMode[] = ["system", "dark", "light"];
export const ACCENT_OPTIONS: AccentColor[] = ["slate", "cyan", "emerald", "amber", "rose", "indigo"];

export const APPEARANCE_KEYS = {
  theme: "scx_theme",
  accent: "scx_accent",
} as const;

function prefersDarkMode() {
  if (typeof window === "undefined") return true;
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

export function resolveThemeMode(mode: ThemeMode): "dark" | "light" {
  if (mode === "system") return prefersDarkMode() ? "dark" : "light";
  return mode;
}

export function applyAppearance(mode: ThemeMode, accent: AccentColor) {
  if (typeof document === "undefined") return;
  const resolved = resolveThemeMode(mode);
  const root = document.documentElement;
  root.dataset.theme = mode;
  root.dataset.themeResolved = resolved;
  root.dataset.accent = accent;
}

