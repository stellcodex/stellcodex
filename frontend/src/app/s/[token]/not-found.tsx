import Link from "next/link";

export default function ShareTokenNotFound() {
  return (
    <main className="grid min-h-screen place-items-center bg-[#0b1220] px-4 text-white">
      <div className="w-full max-w-md rounded-2xl border border-[#334155] bg-[#0f172a] p-6">
        <div className="text-lg font-semibold text-[#fca5a5]">404 Share Not Found</div>
        <p className="mt-2 text-sm text-[#cbd5e1]">Paylaşım bağlantısı geçersiz veya kaldırılmış.</p>
        <Link href="/" className="mt-4 inline-flex rounded-lg border border-[#334155] bg-[#111827] px-3 py-2 text-xs font-semibold text-white hover:bg-[#1f2937]">
          Ana Sayfaya Dön
        </Link>
      </div>
    </main>
  );
}

