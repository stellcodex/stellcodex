const KEY = "scx_sidebar_collapsed";
const UI_FLAGS_KEY = "scx_ui_flags";

export type GlobalUiFlags = {
  compactTables: boolean;
};

export function loadSidebarCollapsed() {
  if (typeof window === "undefined") return false;
  return window.localStorage.getItem(KEY) === "1";
}

export function saveSidebarCollapsed(value: boolean) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(KEY, value ? "1" : "0");
}

export function loadUiFlags(): GlobalUiFlags {
  if (typeof window === "undefined") return { compactTables: false };
  try {
    const raw = window.localStorage.getItem(UI_FLAGS_KEY);
    if (!raw) return { compactTables: false };
    const parsed = JSON.parse(raw) as Partial<GlobalUiFlags>;
    return {
      compactTables: Boolean(parsed.compactTables),
    };
  } catch {
    return { compactTables: false };
  }
}

export function saveUiFlags(flags: GlobalUiFlags) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(UI_FLAGS_KEY, JSON.stringify(flags));
}
