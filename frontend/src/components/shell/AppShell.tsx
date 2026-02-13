"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { appRegistry } from "@/data/appRegistry";

type ShellSection = "home" | "apps" | "library";

type ShellUiContextType = {
  focusMode: boolean;
  canFocus: boolean;
  toggleFocusMode: () => void;
  fullMode: boolean;
  toggleFullMode: () => void;
  chatPanelOpen: boolean;
  toggleChatPanel: () => void;
};

const ShellUiContext = createContext<ShellUiContextType>({
  focusMode: false,
  canFocus: false,
  toggleFocusMode: () => undefined,
  fullMode: false,
  toggleFullMode: () => undefined,
  chatPanelOpen: false,
  toggleChatPanel: () => undefined,
});

type SidebarItem = {
  label: string;
  href: string;
  icon: ReactNode;
};

const coreItems: SidebarItem[] = [
  { label: "Yeni Sohbet", href: "/chat", icon: "S" },
  { label: "Dosyalar", href: "/files", icon: "D" },
];

const appItems: SidebarItem[] = appRegistry.map((item) => ({
  label: item.label,
  href: item.href,
  icon: item.shortLabel,
}));

const libraryItems: SidebarItem[] = [
  { label: "Paylaşılanlar", href: "/library/shared", icon: "P" },
  { label: "Şablonlar", href: "/library/templates", icon: "S" },
  { label: "İndirilenler", href: "/library/downloads", icon: "I" },
];

function isActive(pathname: string, href: string) {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

function SidebarLink({
  item,
  collapsed,
  pathname,
  onNavigate,
}: {
  item: SidebarItem;
  collapsed: boolean;
  pathname: string;
  onNavigate: () => void;
}) {
  const active = isActive(pathname, item.href);

  return (
    <Link
      href={item.href}
      title={collapsed ? item.label : undefined}
      onClick={onNavigate}
      className={[
        "group flex h-10 items-center rounded-xl border px-2.5 text-sm transition",
        collapsed ? "justify-center" : "gap-2.5",
        active
          ? "border-[#d5e6ff] border-l-[3px] border-l-[#2563eb] bg-[#ebf3ff] text-[#124796]"
          : "border-transparent text-[#314152] hover:border-[#e2e8f0] hover:bg-[#f6f8fb]",
      ].join(" ")}
    >
      <span className="inline-flex h-6 w-6 items-center justify-center rounded-md border border-[#dce5ef] bg-white text-[11px] font-semibold">
        {item.icon}
      </span>
      {!collapsed ? <span className="truncate">{item.label}</span> : null}
    </Link>
  );
}

export function AppShell({
  children,
  section,
}: {
  children: ReactNode;
  section: ShellSection;
}) {
  const pathname = usePathname() || "/";
  const [mobileOpenPath, setMobileOpenPath] = useState<string | null>(null);
  const [collapsed, setCollapsed] = useState(() => {
    if (typeof window === "undefined") return false;
    return window.localStorage.getItem("sc-sidebar-collapsed") === "1";
  });
  const [fullMode, setFullMode] = useState(() => {
    if (typeof window === "undefined") return false;
    return window.localStorage.getItem("sc-full-mode") === "1";
  });
  const [chatPanelOpen, setChatPanelOpen] = useState(() => {
    if (typeof window === "undefined") return true;
    return window.localStorage.getItem("sc-chat-panel-open") !== "0";
  });
  const canFocus = section === "apps" || section === "library";
  const focusKey = pathname ? `sc-focus:${pathname}` : "sc-focus";
  const [focusByPath, setFocusByPath] = useState<Record<string, boolean>>({});
  const previousCollapsedRef = useRef(collapsed);

  const readFocusFromSession = useCallback((key: string) => {
    if (typeof window === "undefined") return false;
    return window.sessionStorage.getItem(key) === "1";
  }, []);

  const focusMode = canFocus ? (focusByPath[focusKey] ?? readFocusFromSession(focusKey)) : false;
  const canShowChatPanel = section === "apps" || section === "home" || section === "library";
  const effectiveCollapsed = fullMode || focusMode ? true : collapsed;
  const effectiveChatPanelOpen = canShowChatPanel && chatPanelOpen && !fullMode;
  const mobileOpen = mobileOpenPath === pathname;

  useEffect(() => {
    window.localStorage.setItem("sc-sidebar-collapsed", collapsed ? "1" : "0");
  }, [collapsed]);
  useEffect(() => {
    window.localStorage.setItem("sc-full-mode", fullMode ? "1" : "0");
  }, [fullMode]);
  useEffect(() => {
    window.localStorage.setItem("sc-chat-panel-open", chatPanelOpen ? "1" : "0");
  }, [chatPanelOpen]);

  const toggleFocusMode = useCallback(() => {
    if (!canFocus) return;
    const currentFocus = focusByPath[focusKey] ?? readFocusFromSession(focusKey);
    const nextFocus = !currentFocus;

    if (nextFocus) {
      previousCollapsedRef.current = collapsed;
    } else {
      setCollapsed(previousCollapsedRef.current);
    }

    setFocusByPath((prev) => ({
      ...prev,
      [focusKey]: nextFocus,
    }));

    if (typeof window !== "undefined") {
      window.sessionStorage.setItem(focusKey, nextFocus ? "1" : "0");
    }
  }, [canFocus, collapsed, focusByPath, focusKey, readFocusFromSession]);

  const toggleFullMode = useCallback(() => {
    setFullMode((prev) => !prev);
  }, []);

  const toggleChatPanel = useCallback(() => {
    setChatPanelOpen((prev) => !prev);
  }, []);

  const shellUi = useMemo(
    () => ({
      focusMode,
      canFocus,
      toggleFocusMode,
      fullMode,
      toggleFullMode,
      chatPanelOpen: effectiveChatPanelOpen,
      toggleChatPanel,
    }),
    [focusMode, canFocus, toggleFocusMode, fullMode, toggleFullMode, effectiveChatPanelOpen, toggleChatPanel]
  );

  const contentWrapperClass = [
    "w-full",
    fullMode || focusMode
      ? "max-w-none px-2 py-2"
      : section === "apps"
      ? "mx-auto max-w-none px-2 py-2"
      : "mx-auto max-w-[1240px] px-6 py-6",
  ].join(" ");

  const sidebarWidthClass = effectiveCollapsed ? "w-[72px]" : "w-[240px]";

  return (
    <ShellUiContext.Provider value={shellUi}>
      <div
        className={[
          "min-h-screen text-[#101828]",
          section === "apps" ? "bg-white" : "bg-[#f5f7fb]",
        ].join(" ")}
      >
        <header className="fixed inset-x-0 top-0 z-[80] h-16 border-b border-[#e5e7eb] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
          <div className="flex h-full items-center justify-between px-3 sm:px-4">
            <div className="min-w-0 flex items-center gap-2">
              <button
                type="button"
                className="inline-flex h-9 w-9 items-center justify-center rounded-xl border border-[#dbe3ec] bg-white text-[#314152] lg:hidden"
                onClick={() => setMobileOpenPath((prev) => (prev === pathname ? null : pathname))}
                aria-label="Menü"
              >
                <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" aria-hidden>
                  <path d="M4 7h16M4 12h16M4 17h16" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" />
                </svg>
              </button>
              <Link href="/" className="inline-flex h-10 w-10 items-center justify-center overflow-hidden rounded-lg" aria-label="Ana sayfa">
                <Image
                  src="/assets/branding/sc-logo.png"
                  alt="Logo"
                  width={38}
                  height={38}
                  className="h-[38px] w-[38px] object-contain"
                  priority
                />
              </Link>
              <span className="hidden max-w-[28vw] truncate text-sm font-semibold text-[#1f2937] sm:inline">
                STELLCODEX Workspace
              </span>
            </div>

            <div className="flex items-center gap-2">
              {canShowChatPanel ? (
                <button
                  type="button"
                  className="hidden h-9 items-center rounded-lg border border-[#dbe3ec] bg-white px-3 text-xs font-medium text-[#314152] xl:inline-flex"
                  onClick={toggleChatPanel}
                >
                  {effectiveChatPanelOpen ? "Sohbeti Gizle" : "Sohbeti Aç"}
                </button>
              ) : null}
              <button
                type="button"
                className="hidden h-9 items-center rounded-lg border border-[#dbe3ec] bg-white px-3 text-xs font-medium text-[#314152] lg:inline-flex"
                onClick={toggleFullMode}
              >
                {fullMode ? "Standart Görünüm" : "Tam Sayfa"}
              </button>
            </div>
          </div>
        </header>

        <div className="flex pt-16">
          <aside
            className={[
              "fixed left-0 top-16 z-[70] hidden h-[calc(100vh-64px)] border-r border-[#e2e8f0] bg-white transition-all duration-200 lg:flex-col",
              fullMode ? "lg:hidden" : "lg:flex",
              sidebarWidthClass,
            ].join(" ")}
          >
            <div className="flex items-center justify-between px-2 py-2">
              {!effectiveCollapsed ? (
                <span className="px-2 text-xs font-semibold uppercase tracking-[0.12em] text-[#64748b]">Menü</span>
              ) : (
                <span />
              )}
              <button
                type="button"
                className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-[#dbe3ec] text-[#314152] disabled:cursor-not-allowed disabled:opacity-50"
                onClick={() => setCollapsed((prev) => !prev)}
                aria-label="Sidebar daralt"
                disabled={focusMode}
                title={focusMode ? "Odak modunda sidebar sabit daraltılır" : undefined}
              >
                {effectiveCollapsed ? ">" : "<"}
              </button>
            </div>

            <nav className="flex-1 space-y-4 overflow-y-auto px-2 pb-3">
              <div className="space-y-1">
                {coreItems.map((item) => (
                  <SidebarLink
                    key={item.href}
                    item={item}
                    collapsed={effectiveCollapsed}
                    pathname={pathname}
                    onNavigate={() => setMobileOpenPath(null)}
                  />
                ))}
              </div>

              <div>
                {!effectiveCollapsed ? (
                  <div className="px-2 pb-1 text-xs font-semibold uppercase tracking-[0.12em] text-[#64748b]">Uygulamalar</div>
                ) : null}
                <div className="space-y-1">
                  {appItems.map((item) => (
                    <SidebarLink
                      key={item.href}
                      item={item}
                      collapsed={effectiveCollapsed}
                      pathname={pathname}
                      onNavigate={() => setMobileOpenPath(null)}
                    />
                  ))}
                </div>
              </div>

              <div>
                {!effectiveCollapsed ? (
                  <div className="px-2 pb-1 text-xs font-semibold uppercase tracking-[0.12em] text-[#64748b]">Kütüphane</div>
                ) : null}
                <div className="space-y-1">
                  {libraryItems.map((item) => (
                    <SidebarLink
                      key={item.href}
                      item={item}
                      collapsed={effectiveCollapsed}
                      pathname={pathname}
                      onNavigate={() => setMobileOpenPath(null)}
                    />
                  ))}
                </div>
              </div>
            </nav>

            <div className="border-t border-[#e2e8f0] px-2 py-2">
              <div
                className={["flex items-center rounded-xl bg-[#f8fafc] px-2 py-2", effectiveCollapsed ? "justify-center" : "gap-2"].join(" ")}
              >
                <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-[#dbeafe] text-xs font-semibold text-[#1d4ed8]">SC</span>
                {!effectiveCollapsed ? (
                  <div className="min-w-0">
                    <div className="truncate text-sm font-semibold text-[#1f2937]">Stell Codex</div>
                    <div className="truncate text-xs text-[#64748b]">Plus</div>
                  </div>
                ) : null}
              </div>
            </div>
          </aside>

          {mobileOpen ? (
            <div className="fixed inset-0 z-[75] bg-black/30 lg:hidden" onClick={() => setMobileOpenPath(null)}>
              <aside
                className="h-full w-[240px] border-r border-[#e2e8f0] bg-white px-2 py-2"
                onClick={(event) => event.stopPropagation()}
              >
                <div className="pb-2">
                  <button
                    type="button"
                    className="inline-flex h-9 w-full items-center justify-center rounded-lg border border-[#dbe3ec] text-sm text-[#314152]"
                    onClick={() => setMobileOpenPath(null)}
                  >
                    Menüyü Kapat
                  </button>
                </div>
                <div className="space-y-1">
                  {[...coreItems, ...appItems, ...libraryItems].map((item) => (
                    <SidebarLink
                      key={item.href}
                      item={item}
                      collapsed={false}
                      pathname={pathname}
                      onNavigate={() => setMobileOpenPath(null)}
                    />
                  ))}
                </div>
              </aside>
            </div>
          ) : null}

          <main
            className="min-w-0 flex-1"
            style={{
              marginLeft: mobileOpen ? 0 : undefined,
            }}
          >
            <div className={[
              "transition-all duration-200",
              fullMode ? "lg:ml-0" : "lg:ml-[240px]",
              !fullMode && effectiveCollapsed ? "lg:ml-[72px]" : "",
              effectiveChatPanelOpen ? "xl:mr-[320px]" : "xl:mr-0",
            ].join(" ")}>
              <div className={contentWrapperClass}>{children}</div>
            </div>
          </main>

          {effectiveChatPanelOpen ? (
            <aside className="fixed right-0 top-16 z-[60] hidden h-[calc(100vh-64px)] w-[320px] border-l border-[#e2e8f0] bg-white p-3 xl:flex xl:flex-col">
              <div className="flex items-center justify-between border-b border-[#eef2f7] pb-2">
                <h2 className="truncate text-sm font-semibold text-[#1f2937]">Sohbet Paneli</h2>
                <button
                  type="button"
                  onClick={toggleChatPanel}
                  className="inline-flex h-7 items-center rounded-md border border-[#dbe3ec] px-2 text-xs text-[#314152]"
                >
                  Gizle
                </button>
              </div>
              <div className="min-h-0 flex-1 overflow-y-auto py-3">
                <p className="text-sm text-[#475569]">
                  Hızlı erişim için sohbet paneli açık. Tüm mesaj akışı için sohbet sayfasını kullanın.
                </p>
                <div className="mt-3 space-y-2">
                  {["Dosya yükleme adımları", "3D görünüm kontrolleri", "Render hazırlığı", "Proje akışı"].map((item) => (
                    <button
                      key={item}
                      type="button"
                      className="w-full rounded-lg border border-[#dbe3ec] bg-[#f8fafc] px-3 py-2 text-left text-xs text-[#334155]"
                    >
                      {item}
                    </button>
                  ))}
                </div>
              </div>
              <Link
                href="/chat"
                className="inline-flex h-10 items-center justify-center rounded-lg border border-[#1d4ed8] bg-[#2563eb] px-3 text-sm font-semibold text-white hover:bg-[#1d4ed8]"
              >
                Sohbet Sayfasına Git
              </Link>
            </aside>
          ) : null}
        </div>
      </div>
    </ShellUiContext.Provider>
  );
}

export function useShellUi() {
  return useContext(ShellUiContext);
}
