import type { Metadata } from "next";
import "./globals.css";
import { UserProvider } from "@/context/UserContext";

export const metadata: Metadata = {
  title: "STELLCODEX",
  description: "Industrial files, projects, and application workflows in one workspace.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const resolvedTheme = "light";
  const themeBootScript = `(()=>{const d=document.documentElement;d.dataset.theme='light';d.dataset.themeResolved='light';})();`;

  return (
    <html lang="en" suppressHydrationWarning>
      <body data-theme={resolvedTheme}>
        <script dangerouslySetInnerHTML={{ __html: themeBootScript }} />
        <UserProvider>{children}</UserProvider>
      </body>
    </html>
  );
}
