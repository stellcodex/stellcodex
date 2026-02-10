import "./globals.css";

import Sidebar from "@/components/Sidebar";
import { UserProvider } from "@/context/UserContext";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="tr">
      <body className="min-h-screen bg-[#F7F8FA] text-[#111827]">
        <UserProvider>
          <div className="flex min-h-screen flex-col">
            <Sidebar />
            <main className="order-1 pb-24 md:ml-[280px]">
              {children}
            </main>
          </div>
        </UserProvider>
      </body>
    </html>
  );
}
