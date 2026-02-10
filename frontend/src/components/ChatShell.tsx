"use client";

import { useEffect, useRef, useState } from "react";

type Message = {
  id: string;
  role: "user" | "system";
  text: string;
};

export default function ChatShell() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const endRef = useRef<HTMLDivElement | null>(null);

  const addMessage = (text: string, role: "user" | "system") => {
    setMessages((prev) => [
      ...prev,
      {
        id: `${role}-${Date.now()}-${Math.random().toString(36).slice(2)}`,
        role,
        text,
      },
    ]);
  };

  useEffect(() => {
    const handleIntent = (event: Event) => {
      const custom = event as CustomEvent<{ query: string }>;
      if (!custom.detail?.query) {
        return;
      }
      addMessage(custom.detail.query, "user");
    };

    window.addEventListener("chat-intent", handleIntent);
    return () => window.removeEventListener("chat-intent", handleIntent);
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    const trimmed = input.trim();
    if (!trimmed) {
      return;
    }
    addMessage(trimmed, "user");
    setInput("");
  };

  return (
    <section className="order-2 rounded-2xl border border-[#E5E7EB] bg-white shadow-sm">
      <div className="flex h-[380px] flex-col">
        <div className="flex-1 space-y-3 overflow-y-auto px-5 py-4">
          {messages.length === 0 && (
            <div className="rounded-2xl border border-dashed border-[#E5E7EB] bg-[#F7F8FA] px-4 py-6 text-sm text-[#6B7280]">
              Sohbet burada baslar. Bir mesaj yazarak devam edin.
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[70%] rounded-2xl px-4 py-2 text-sm ${
                  message.role === "user"
                    ? "bg-[#E5E7EB] text-[#111827]"
                    : "bg-[#F7F8FA] text-[#111827]"
                }`}
              >
                {message.text}
              </div>
            </div>
          ))}
          <div ref={endRef} />
        </div>

        <form
          onSubmit={handleSubmit}
          className="border-t border-[#E5E7EB] px-4 py-3"
        >
          <input
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Mesaj yaz..."
            className="w-full rounded-xl border border-[#E5E7EB] bg-white px-4 py-3 text-sm text-[#111827] outline-none placeholder:text-[#6B7280]"
          />
        </form>
      </div>
    </section>
  );
}
