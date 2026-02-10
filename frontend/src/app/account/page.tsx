"use client";

import { useState } from "react";
import { useUser } from "@/context/UserContext";

export default function AccountPage() {
  const { user, login } = useUser();
  const [name, setName] = useState("");

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) {
      return;
    }
    login({ id: `${Date.now()}`, name: trimmed });
    setName("");
  };

  return (
    <section className="space-y-6">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold text-[#111827]">Hesap sayfası</h1>
        <p className="text-sm text-[#6B7280]">
          Bu sayfa daha sonra backend auth ile bağlanacak.
        </p>
      </header>

      <div className="rounded-2xl border border-[#E5E7EB] bg-white p-6 shadow-sm">
        <p className="text-sm font-medium text-[#111827]">Giriş yap</p>
        <p className="mt-1 text-xs text-[#6B7280]">
          Şimdilik sadece isim girerek giriş yapabilirsiniz.
        </p>

        <form onSubmit={handleSubmit} className="mt-4 space-y-3">
          <input
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="Adınız"
            className="w-full rounded-xl border border-[#E5E7EB] bg-[#F7F8FA] px-4 py-3 text-sm text-[#111827] outline-none placeholder:text-[#6B7280]"
          />
          <button
            type="submit"
            className="w-full rounded-xl bg-[#0055FF] px-4 py-3 text-sm font-semibold text-white"
          >
            Login
          </button>
        </form>

        {user && (
          <div className="mt-4 rounded-xl border border-[#E5E7EB] bg-[#F7F8FA] px-4 py-3 text-sm text-[#111827]">
            Aktif kullanıcı: {user.name}
          </div>
        )}
      </div>
    </section>
  );
}
