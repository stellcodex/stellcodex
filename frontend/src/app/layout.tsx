import "./globals.css";
import type { Metadata } from "next";
import { cookies } from "next/headers";

import { UserProvider } from "@/context/UserContext";

export const metadata: Metadata = {
  title: "STELLCODEX",
  description: "2D ve 3D mühendislik görüntüleyicisi",
  manifest: "/site.webmanifest",
  icons: {
    icon: [
      { url: "/favicon.ico" },
      { url: "/stellcodex-logo.png", type: "image/png" },
    ],
    shortcut: "/stellcodex-logo.png",
    apple: "/stellcodex-logo.png",
  },
};

function normalizeTheme(value: string | undefined) {
  if (value === "system" || value === "light" || value === "dark") return value;
  return "light";
}

function normalizeAccent(value: string | undefined) {
  if (value === "slate" || value === "cyan" || value === "emerald" || value === "amber" || value === "rose" || value === "indigo") {
    return value;
  }
  return "cyan";
}

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const cookieStore = await cookies();
  const theme = normalizeTheme(cookieStore.get("scx_theme")?.value);
  const accent = normalizeAccent(cookieStore.get("scx_accent")?.value);
  const resolvedTheme = theme === "system" ? "light" : theme;
  const initScript = `(function(){try{var d=document.documentElement;var t=localStorage.getItem('scx_theme')||'${theme}';var a=localStorage.getItem('scx_accent')||'${accent}';if(!t){t='light';}if(!a){a='cyan';}d.dataset.theme=t;d.dataset.accent=a;var r=t==='system'?(window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'):t;d.dataset.themeResolved=r;}catch(e){}})();`;

  return (
    <html lang="tr" data-theme={theme} data-theme-resolved={resolvedTheme} data-accent={accent} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: initScript }} />
      </head>
      <body className="min-h-screen bg-bg text-text">
        <UserProvider>{children}</UserProvider>
      </body>
    </html>
  );
}
