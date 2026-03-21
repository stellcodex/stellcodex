import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "STELLCODEX",
  description: "Deterministic manufacturing decision platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
