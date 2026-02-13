"use client";

import { LayoutShell } from "@/components/layout/LayoutShell";
import { ChatComposer } from "@/components/chat/ChatComposer";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { useState } from "react";

const initialMessages = [
  { role: "assistant" as const, content: "Merhaba. Nasıl yardımcı olabilirim?" },
  { role: "user" as const, content: "DXF katmanları hakkında özet çıkar." },
  { role: "assistant" as const, content: "Katmanlar renk ve tip ile listeleniyor. Seçime göre render alırsınız." },
];

export default function ChatThreadPage() {
  const [messages, setMessages] = useState(initialMessages);

  return (
    <LayoutShell>
      <div className="flex h-full flex-col gap-sectionGap">
        <div className="text-fs2 font-semibold">Sohbet</div>
        <div className="flex-1 space-y-sp2 overflow-y-auto rounded-r2 border-soft bg-surface px-cardPad py-cardPad">
          {messages.map((m, idx) => (
            <MessageBubble key={idx} role={m.role} content={m.content} />
          ))}
        </div>
        <ChatComposer
          onSend={(value) =>
            setMessages((prev) => [...prev, { role: "user", content: value }])
          }
        />
      </div>
    </LayoutShell>
  );
}
