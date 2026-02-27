import "./globals.css";
import type { Metadata } from "next";

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

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="tr">
      <body className="min-h-screen bg-bg text-text">
        <UserProvider>{children}</UserProvider>
      </body>
    </html>
  );
}
