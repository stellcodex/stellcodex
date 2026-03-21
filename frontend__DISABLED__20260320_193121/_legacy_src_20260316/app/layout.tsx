import "./globals.css";
import type { Metadata } from "next";
import { cookies } from "next/headers";

import { UserProvider } from "@/context/UserContext";

export const metadata: Metadata = {
  title: "STELLCODEX",
  description: "2D and 3D engineering workspace",
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
  return "light";
}

function normalizeAccent(value: string | undefined) {
  if (value === "slate" || value === "cyan" || value === "emerald" || value === "amber" || value === "rose" || value === "indigo") {
    return value;
  }
  return "emerald";
}

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const cookieStore = await cookies();
  const theme = normalizeTheme(cookieStore.get("scx_theme")?.value);
  const accent = normalizeAccent(cookieStore.get("scx_accent")?.value);
  const resolvedTheme = "light";
  const initScript = `(function(){try{var d=document.documentElement;var a=localStorage.getItem('scx_accent')||'${accent}';d.dataset.theme='light';d.dataset.themeResolved='light';d.dataset.accent=a||'emerald';}catch(e){}})();`;

  return (
    <html lang="en" data-theme={theme} data-theme-resolved={resolvedTheme} data-accent={accent} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: initScript }} />
      </head>
      <body className="min-h-screen bg-bg text-text">
        <UserProvider>{children}</UserProvider>
      </body>
    </html>
  );
}
