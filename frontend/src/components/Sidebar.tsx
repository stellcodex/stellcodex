"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { JSX, ReactNode } from "react";
import { useUser } from "@/context/UserContext";
import { appRegistry } from "@/data/appRegistry";

type IconType = (props: { className?: string }) => JSX.Element;

type NavLinkItem = {
  label: string;
  href: string;
  icon: IconType;
  requiresAuth?: boolean;
};

const navItems: NavLinkItem[] = [
  { label: "Yeni Sohbet", href: "/", icon: IconChat },
  { label: "Genel Arama", href: "/", icon: IconSearch },
];

const appItems: NavLinkItem[] = appRegistry.map((item) => ({
  label: item.label,
  href: item.href,
  icon:
    item.key === "3d"
      ? IconCube
      : item.key === "2d"
      ? IconDraft
      : item.key === "render"
      ? IconSpark
      : item.key === "exploded"
      ? IconBurst
      : IconSpark,
}));

const userItems: NavLinkItem[] = [
  { label: "Dosyalarım", href: "/files", icon: IconFiles, requiresAuth: true },
  { label: "Projelerim", href: "/projects", icon: IconFolder, requiresAuth: true },
];

const footerItems: NavLinkItem[] = [
  { label: "Ayarlar", href: "/settings", icon: IconSettings, requiresAuth: true },
  { label: "Hesap", href: "/account", icon: IconUser, requiresAuth: true },
];

const mobileItems: NavLinkItem[] = [
  { label: "Ana Sayfa", href: "/", icon: IconHome },
  ...appItems,
  ...userItems,
  ...footerItems,
];

export default function Sidebar() {
  const pathname = usePathname() || "/";
  const { isAuthenticated } = useUser();

  const isActive = (href: string) => {
    if (href === "/") {
      return pathname === "/";
    }
    return pathname.startsWith(href);
  };

  return (
    <>
      <aside className="hidden md:fixed md:left-0 md:top-0 md:flex md:h-screen md:w-[280px] md:flex-col md:justify-between md:border-r md:border-[#E5E7EB] md:bg-white md:px-4 md:py-6">
        <div>
          <Link href="/" className="flex items-center gap-3 px-2">
            <LogoIcon />
            <span className="text-base font-semibold text-[#111827]">STELLCODEX</span>
          </Link>

          <div className="mt-6 space-y-2">
            {navItems.map((item) => (
              <NavItem
                key={item.label}
                href={item.href}
                label={item.label}
                icon={item.icon}
                active={isActive(item.href)}
              />
            ))}
          </div>

          <div className="mt-6">
            <div className="px-3 text-xs font-semibold uppercase tracking-[0.2em] text-[#6B7280]">
              Uygulamalar
            </div>
            <div className="mt-3 space-y-2">
              {appItems.map((item) => (
                <NavItem
                  key={item.label}
                  href={item.href}
                  label={item.label}
                  icon={item.icon}
                  active={isActive(item.href)}
                />
              ))}
            </div>
          </div>

          <div className="mt-6">
            <div className="px-3 text-xs font-semibold uppercase tracking-[0.2em] text-[#6B7280]">
              Kullanıcı Alanı
            </div>
            <div className="mt-3 space-y-2">
              {userItems.map((item) => (
                <NavItem
                  key={item.label}
                  href={item.requiresAuth && !isAuthenticated ? "/account" : item.href}
                  label={item.label}
                  icon={item.icon}
                  active={isActive(item.href)}
                />
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-2">
          {footerItems.map((item) => (
            <NavItem
              key={item.label}
              href={item.requiresAuth && !isAuthenticated ? "/account" : item.href}
              label={item.label}
              icon={item.icon}
              active={isActive(item.href)}
            />
          ))}
        </div>
      </aside>

      <nav className="fixed bottom-0 left-0 right-0 z-50 flex h-[60px] items-center gap-4 overflow-x-auto border-t border-[#E5E7EB] bg-white px-4 md:hidden">
        {mobileItems.map((item) => {
          const active = isActive(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.label}
              href={item.href}
              className={`flex h-11 w-11 items-center justify-center rounded-xl border border-transparent ${
                active
                  ? "bg-[#0055FF] text-white"
                  : "text-[#6B7280] hover:bg-[#F7F8FA]"
              }`}
              aria-label={item.label}
            >
              <Icon className={active ? "text-[#CFE0FF]" : "text-[#6B7280]"} />
            </Link>
          );
        })}
      </nav>
    </>
  );
}

function NavItem({
  href,
  label,
  icon: Icon,
  active,
}: {
  href: string;
  label: string;
  icon: IconType;
  active: boolean;
}) {
  return (
    <Link
      href={href}
      className={`group flex items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium transition ${
        active
          ? "bg-[#0055FF] text-white"
          : "text-[#6B7280] hover:bg-[#F7F8FA]"
      }`}
    >
      <Icon className={active ? "text-[#CFE0FF]" : "text-[#6B7280]"} />
      <span>{label}</span>
    </Link>
  );
}

function LogoIcon() {
  return (
    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#0055FF] text-sm font-semibold text-white">
      SC
    </div>
  );
}

function IconBase({ className, children }: { className?: string; children: ReactNode }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={`h-5 w-5 ${className ?? ""}`}
    >
      {children}
    </svg>
  );
}

function IconHome({ className }: { className?: string }) {
  return (
    <IconBase className={className}>
      <path d="M3 11.5L12 4l9 7.5" />
      <path d="M6 10.5V20h12v-9.5" />
    </IconBase>
  );
}

function IconChat({ className }: { className?: string }) {
  return (
    <IconBase className={className}>
      <path d="M4 5h16v10H7l-3 4V5z" />
    </IconBase>
  );
}

function IconSearch({ className }: { className?: string }) {
  return (
    <IconBase className={className}>
      <circle cx="11" cy="11" r="6" />
      <path d="m20 20-3.5-3.5" />
    </IconBase>
  );
}

function IconCube({ className }: { className?: string }) {
  return (
    <IconBase className={className}>
      <path d="M12 3 4 7v10l8 4 8-4V7l-8-4z" />
      <path d="M4 7l8 4 8-4" />
      <path d="M12 11v10" />
    </IconBase>
  );
}

function IconDraft({ className }: { className?: string }) {
  return (
    <IconBase className={className}>
      <path d="M4 4h10l6 6v10H4z" />
      <path d="M14 4v6h6" />
    </IconBase>
  );
}

function IconSpark({ className }: { className?: string }) {
  return (
    <IconBase className={className}>
      <path d="M12 2v6" />
      <path d="M12 16v6" />
      <path d="M4 12h6" />
      <path d="M14 12h6" />
      <path d="M6 6l4 4" />
      <path d="M14 14l4 4" />
      <path d="M18 6l-4 4" />
      <path d="M10 14l-4 4" />
    </IconBase>
  );
}

function IconBurst({ className }: { className?: string }) {
  return (
    <IconBase className={className}>
      <path d="M12 3v18" />
      <path d="M3 12h18" />
      <path d="m5.5 5.5 13 13" />
      <path d="m18.5 5.5-13 13" />
    </IconBase>
  );
}

function IconFiles({ className }: { className?: string }) {
  return (
    <IconBase className={className}>
      <path d="M4 7h8l2 2h6v10H4z" />
      <path d="M4 7V5h8" />
    </IconBase>
  );
}

function IconFolder({ className }: { className?: string }) {
  return (
    <IconBase className={className}>
      <path d="M3 7h6l2 2h10v10H3z" />
    </IconBase>
  );
}

function IconSettings({ className }: { className?: string }) {
  return (
    <IconBase className={className}>
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a7.6 7.6 0 0 0 .1-2l2-1.1-2-3.4-2.3.6a7.2 7.2 0 0 0-1.7-1l-.3-2.4H9.1l-.3 2.4a7.2 7.2 0 0 0-1.7 1l-2.3-.6-2 3.4 2 1.1a7.6 7.6 0 0 0 .1 2l-2 1.1 2 3.4 2.3-.6a7.2 7.2 0 0 0 1.7 1l.3 2.4h5.8l.3-2.4a7.2 7.2 0 0 0 1.7-1l2.3.6 2-3.4-2-1.1z" />
    </IconBase>
  );
}

function IconUser({ className }: { className?: string }) {
  return (
    <IconBase className={className}>
      <circle cx="12" cy="8" r="4" />
      <path d="M4 20c2.5-4 13.5-4 16 0" />
    </IconBase>
  );
}
