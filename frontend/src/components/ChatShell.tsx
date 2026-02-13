"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getLatestWorkspaceFile, listWorkspaceFiles } from "@/lib/workspace-store";

type Message = {
  id: string;
  role: "user" | "assistant";
  text: string;
};

function createId(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function botReply(input: string) {
  const text = input.trim().toLowerCase();
  const files = listWorkspaceFiles();
  const latest = getLatestWorkspaceFile();

  if (!text) {
    return "Sorunuzu biraz daha detaylandırın, adım adım yönlendireyim.";
  }

  if (text.includes("nasıl kullan") || text.includes("nereden başla") || text.includes("ilk adım")) {
    return [
      "STELLCODEX hızlı başlangıç:",
      "1. `Dosya Yükle` ile modelinizi yükleyin.",
      "2. Dosya tipine göre sistem sizi 3D veya 2D moduna taşır.",
      "3. Sol menüden Patlatma/Render/MoldCodes modlarını açın.",
      "4. Gerekirse Projeler bölümünden aynı dosyayı tekrar çağırın.",
    ].join("\n");
  }

  if (text.includes("dosya") && text.includes("yük")) {
    return [
      "Dosya yükleme için izlenecek yol:",
      "1. Ana ekrandaki grid alana dosyayı sürükleyin veya `Dosya Yükle` deyin.",
      "2. Yükleme tamamlanınca dosya otomatik projeye eklenir.",
      "3. 3D dosya ise `/app/3d`, 2D dosya ise `/app/2d` açılır.",
    ].join("\n");
  }

  if (text.includes("proje")) {
    if (!files.length) {
      return "Henüz proje kaydı yok. Dosya yüklediğinizde otomatik olarak `Genel Proje` içine eklenir.";
    }
    return `Toplam ${files.length} dosyanız proje akışına kaydedildi. Projeler sayfasından dosya bazlı açabilirsiniz.`;
  }

  if (text.includes("3d")) {
    return "3D için sol menüden `3D Model` açın. Dosya seçiliyse görüntüleyici alanında modeliniz doğrudan açılır.";
  }

  if (text.includes("2d") || text.includes("dxf")) {
    return "2D/DXF için `2D DXF` modunu açın. Ölçü, katman ve görünüm araçları bu modda kullanılır.";
  }

  if (text.includes("patlat")) {
    return "Patlatma modunda montajı adımlı olarak ayırabilir, odak ve kesit kontrolleriyle bileşen ilişkisini inceleyebilirsiniz.";
  }

  if (text.includes("render")) {
    return "Render modunda önce dosyayı seçin, sonra preset belirleyip `Render Başlat` ile kuyruğa alın.";
  }

  if (text.includes("moldcodes")) {
    return "MoldCodes bölümünde kategori ve arama ile standart elemanları tarayıp teknik özet panelinden kontrol edebilirsiniz.";
  }

  if (text.includes("kütüphane") || text.includes("paylaş")) {
    return "Kütüphane akışında dosyaları paylaşabilir, şablonları görebilir ve indirilenleri ayrı sekmelerde yönetebilirsiniz.";
  }

  if (text.includes("son dosya") || text.includes("en son dosya") || text.includes("ne yükledim")) {
    if (!latest) return "Henüz kayıtlı bir yükleme yok.";
    return `Son yüklenen dosya: ${latest.originalFilename} (${latest.mode.toUpperCase()}). İstersen bu dosyayı ilgili modda açmana yardımcı olayım.`;
  }

  return "Bunu netleştirelim: dosya yükleme, 3D/2D görüntüleme, proje yönetimi veya render adımından hangisinde yardıma ihtiyacınız var?";
}

export default function ChatShell() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: createId("assistant"),
      role: "assistant",
      text: "Merhaba. STELLCODEX kullanımında size adım adım yardımcı olabilirim. Dosya yükleme, 3D/2D görüntüleme, proje ve render konularında soru sorabilirsiniz.",
    },
  ]);
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);
  const [viewportHeight, setViewportHeight] = useState(0);
  const endRef = useRef<HTMLDivElement | null>(null);

  const pushMessage = useCallback((role: Message["role"], text: string) => {
    setMessages((prev) => [...prev, { id: createId(role), role, text }]);
  }, []);

  const submitUserMessage = useCallback(
    (raw: string) => {
      const trimmed = raw.trim();
      if (!trimmed) return;

      pushMessage("user", trimmed);
      setTyping(true);

      window.setTimeout(() => {
        pushMessage("assistant", botReply(trimmed));
        setTyping(false);
      }, 320);
    },
    [pushMessage]
  );

  useEffect(() => {
    const handleIntent = (event: Event) => {
      const custom = event as CustomEvent<{ query: string }>;
      if (!custom.detail?.query) return;
      submitUserMessage(custom.detail.query);
    };

    window.addEventListener("chat-intent", handleIntent);
    return () => window.removeEventListener("chat-intent", handleIntent);
  }, [submitUserMessage]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, typing]);

  useEffect(() => {
    const updateHeight = () => {
      const vvHeight = typeof window !== "undefined" ? window.visualViewport?.height : undefined;
      setViewportHeight(Math.floor(vvHeight || window.innerHeight));
    };

    updateHeight();
    window.addEventListener("resize", updateHeight);
    window.visualViewport?.addEventListener("resize", updateHeight);
    window.visualViewport?.addEventListener("scroll", updateHeight);
    return () => {
      window.removeEventListener("resize", updateHeight);
      window.visualViewport?.removeEventListener("resize", updateHeight);
      window.visualViewport?.removeEventListener("scroll", updateHeight);
    };
  }, []);

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    const value = input.trim();
    if (!value) return;
    submitUserMessage(value);
    setInput("");
  };

  const shellHeight = Math.max(420, (viewportHeight || 820) - 180);

  return (
    <section className="rounded-2xl border border-[#E5E7EB] bg-white shadow-sm">
      <div className="flex min-h-[420px] flex-col overflow-hidden" style={{ height: shellHeight }}>
        <div className="flex-1 space-y-3 overflow-y-auto overscroll-contain px-5 py-4 pb-24">
          {messages.map((message) => (
            <div key={message.id} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-[82%] whitespace-pre-line rounded-2xl px-4 py-2 text-sm ${
                  message.role === "user" ? "bg-[#E5E7EB] text-[#111827]" : "bg-[#F7F8FA] text-[#111827]"
                }`}
              >
                {message.text}
              </div>
            </div>
          ))}

          {typing ? (
            <div className="flex justify-start">
              <div className="rounded-2xl bg-[#F7F8FA] px-4 py-2 text-sm text-[#6B7280]">Yazıyor...</div>
            </div>
          ) : null}
          <div ref={endRef} />
        </div>

        <form
          onSubmit={handleSubmit}
          className="sticky bottom-0 border-t border-[#E5E7EB] bg-white px-4 py-3"
          style={{ paddingBottom: "max(env(safe-area-inset-bottom), 12px)" }}
        >
          <input
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Mesaj yaz... (örn: 3D dosyamı nasıl açarım?)"
            className="w-full rounded-xl border border-[#E5E7EB] bg-white px-4 py-3 text-sm text-[#111827] outline-none placeholder:text-[#6B7280]"
          />
        </form>
      </div>
    </section>
  );
}
