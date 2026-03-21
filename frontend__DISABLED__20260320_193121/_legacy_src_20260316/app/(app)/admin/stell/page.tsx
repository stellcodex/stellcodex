"use client";

import { useState, useRef, useEffect, KeyboardEvent } from "react";

interface Message {
  role: "user" | "stell";
  text: string;
  ts: string;
}

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem("scx_token");
}

async function sendToStell(message: string): Promise<string> {
  const token = getToken();
  const res = await fetch("/api/v1/stell/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ message }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Error: ${res.status}`);
  }
  const data = await res.json();
  return data.reply as string;
}

function now() {
  return new Date().toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
}

export default function StellChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    { role: "stell", text: "Hello. I am Stell, the Stellcodex assistant.\nType `help` for available commands.", ts: now() },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send() {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", text, ts: now() }]);
    setLoading(true);
    try {
      const reply = await sendToStell(text);
      setMessages((m) => [...m, { role: "stell", text: reply, ts: now() }]);
    } catch (e: any) {
      setMessages((m) => [...m, { role: "stell", text: `❌ ${e.message}`, ts: now() }]);
    } finally {
      setLoading(false);
    }
  }

  function onKey(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] max-w-3xl mx-auto">
      <div className="mb-4">
        <h1 className="text-xl font-semibold text-slate-900">Stell Assistant</h1>
        <p className="text-sm text-slate-500">
          Use Stell for platform operations, note taking, and knowledge queries.
        </p>
      </div>

      <div className="flex-1 overflow-y-auto rounded-2xl border border-slate-200 bg-white p-4 space-y-3">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex gap-2 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}
          >
            <div
              className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                msg.role === "stell"
                  ? "bg-slate-900 text-white"
                  : "bg-blue-600 text-white"
              }`}
            >
              {msg.role === "stell" ? "S" : "A"}
            </div>
            <div className={`max-w-[75%] ${msg.role === "user" ? "items-end" : "items-start"} flex flex-col gap-1`}>
              <div
                className={`rounded-2xl px-4 py-2.5 text-sm whitespace-pre-wrap leading-relaxed ${
                  msg.role === "stell"
                    ? "bg-slate-100 text-slate-800 rounded-tl-sm"
                    : "bg-blue-600 text-white rounded-tr-sm"
                }`}
              >
                {msg.text}
              </div>
              <span className="text-[10px] text-slate-400 px-1">{msg.ts}</span>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex gap-2">
            <div className="w-8 h-8 rounded-full bg-slate-900 flex items-center justify-center text-sm font-bold text-white flex-shrink-0">
              S
            </div>
            <div className="bg-slate-100 rounded-2xl rounded-tl-sm px-4 py-2.5 text-sm text-slate-500">
              <span className="animate-pulse">Stell is typing...</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="mt-3 flex gap-2 items-end">
        <textarea
          className="flex-1 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-slate-900 placeholder:text-slate-400"
          rows={1}
          placeholder="Message Stell... (Enter to send, Shift+Enter for a new line)"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKey}
          disabled={loading}
        />
        <button
          onClick={send}
          disabled={loading || !input.trim()}
          className="flex-shrink-0 h-11 w-11 rounded-2xl bg-slate-900 text-white flex items-center justify-center disabled:opacity-40 hover:bg-slate-700 transition"
          aria-label="Send"
        >
          ↑
        </button>
      </div>
      <p className="mt-1.5 text-center text-[10px] text-slate-400">
        Commands: <code>status</code> · <code>note: ...</code> · <code>log: backend</code> · <code>knowledge: platform</code> · <code>help</code>
      </p>
    </div>
  );
}
