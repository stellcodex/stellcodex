const KEY = "scx_sidebar_collapsed";

export function loadSidebarCollapsed() {
  if (typeof window === "undefined") return false;
  return window.localStorage.getItem(KEY) === "1";
}

export function saveSidebarCollapsed(value: boolean) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(KEY, value ? "1" : "0");
}
