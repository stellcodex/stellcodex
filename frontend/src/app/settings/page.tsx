"use client";

import { useUser } from "@/context/UserContext";

export default function SettingsPage() {
  const { user, logout } = useUser();

  return (
    <section className="space-y-6">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold text-[#111827]">Ayarlar</h1>
        <p className="text-sm text-[#6B7280]">
          Bu sayfa daha sonra backend auth ile bağlanacak.
        </p>
      </header>

      <div className="rounded-2xl border border-[#E5E7EB] bg-white p-6 shadow-sm">
        <p className="text-sm text-[#6B7280]">
          Oturum durumunu yönetmek için aşağıdaki butonu kullanın.
        </p>
        <button
          type="button"
          onClick={logout}
          className="mt-4 rounded-xl border border-[#E5E7EB] bg-[#F7F8FA] px-4 py-3 text-sm font-semibold text-[#111827]"
        >
          Logout
        </button>
        {user && (
          <p className="mt-3 text-xs text-[#6B7280]">Aktif kullanıcı: {user.name}</p>
        )}
      </div>
    </section>
  );
}
