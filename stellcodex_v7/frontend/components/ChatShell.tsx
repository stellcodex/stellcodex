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

  // Keep a small bilingual keyword set here so quick-start prompts work for
  // both English and Turkish users without changing the underlying workflow.
  if (!text) {
    return "Add a little more detail and I will guide you step by step.";
  }

  if (
    text.includes("how to use") ||
    text.includes("where to start") ||
    text.includes("first step") ||
    text.includes("nasıl kullan") ||
    text.includes("nereden başla") ||
    text.includes("ilk adım")
  ) {
    return [
      "STELLCODEX quick start:",
      "1. Upload the model with `Upload File`.",
      "2. The system routes you into 3D or 2D mode based on the file type.",
      "3. Open Exploded View, Render, or MoldCodes from the left navigation.",
      "4. Reopen the same file from Projects whenever you need it.",
    ].join("\n");
  }

  if ((text.includes("file") && text.includes("upload")) || (text.includes("dosya") && text.includes("yük"))) {
    return [
      "Upload flow:",
      "1. Drag the file into the main drop zone or click `Upload File`.",
      "2. The uploaded file is added to the active project automatically.",
      "3. 3D files open in `/app/3d`, and 2D files open in `/app/2d`.",
    ].join("\n");
  }

  if (text.includes("project") || text.includes("proje")) {
    if (!files.length) {
      return "There is no project record yet. Uploaded files are added to the default project automatically.";
    }
    return `${files.length} files are already registered in the project flow. You can reopen them from the Projects page.`;
  }

  if (text.includes("3d")) {
    return "Open `3D Model` from the left navigation. If a file is selected, the model opens directly in the viewer surface.";
  }

  if (text.includes("2d") || text.includes("dxf")) {
    return "Open `2D DXF` for drawings. Measurement, layer, and view tools are available in that mode.";
  }

  if (text.includes("explode") || text.includes("patlat")) {
    return "Exploded View lets you separate the assembly step by step and inspect component relationships with focus and section controls.";
  }

  if (text.includes("render")) {
    return "In Render mode, select a file first, then choose a preset and start the render job.";
  }

  if (text.includes("moldcodes")) {
    return "In MoldCodes, browse standard components by category and search, then review them in the technical summary panel.";
  }

  if (text.includes("library") || text.includes("share") || text.includes("kütüphane") || text.includes("paylaş")) {
    return "The library flow lets you share files, review templates, and manage downloads in separate tabs.";
  }

  if (
    text.includes("latest file") ||
    text.includes("last file") ||
    text.includes("son dosya") ||
    text.includes("en son dosya") ||
    text.includes("ne yükledim")
  ) {
    if (!latest) return "There is no recorded upload yet.";
    return `Latest uploaded file: ${latest.originalFilename} (${latest.mode.toUpperCase()}). I can help you open it in the correct mode.`;
  }

  return "Let’s narrow it down: do you need help with upload flow, 3D or 2D viewing, project management, or rendering?";
}

export default function ChatShell() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: createId("assistant"),
      role: "assistant",
      text: "Hello. I can guide you through STELLCODEX step by step. Ask about upload flow, 3D or 2D viewing, projects, or rendering.",
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
              <div className="rounded-2xl bg-[#F7F8FA] px-4 py-2 text-sm text-[#6B7280]">Typing...</div>
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
            placeholder="Ask anything... (for example: how do I open my 3D file?)"
            className="w-full rounded-xl border border-[#E5E7EB] bg-white px-4 py-3 text-sm text-[#111827] outline-none placeholder:text-[#6B7280]"
          />
        </form>
      </div>
    </section>
  );
}
