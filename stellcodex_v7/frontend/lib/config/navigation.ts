export type NavigationItem = {
  href: string;
  label: string;
};

export const primaryNavigation: NavigationItem[] = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/projects", label: "Projects" },
  { href: "/files", label: "Files" },
  { href: "/shares", label: "Shares" },
  { href: "/admin", label: "Admin" },
  { href: "/settings", label: "Settings" },
];
