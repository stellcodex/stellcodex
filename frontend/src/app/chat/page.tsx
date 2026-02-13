import ChatShell from "@/components/ChatShell";
import { AppShell } from "@/components/shell/AppShell";

export default function ChatPage() {
  return (
    <AppShell section="home">
      <div className="space-y-4">
        <div className="rounded-2xl border border-[#e2e8f0] bg-white px-4 py-4 shadow-[0_1px_2px_rgba(16,24,40,0.04)]">
          <h1 className="text-2xl font-semibold tracking-[-0.01em] text-[#0f172a]">Yeni Sohbet</h1>
          <p className="mt-2 text-sm text-[#475569]">
            Dosya yükleme, görüntüleme, proje yönetimi ve render adımlarında size yönlendirme yaparım.
          </p>
        </div>
        <ChatShell />
      </div>
    </AppShell>
  );
}
