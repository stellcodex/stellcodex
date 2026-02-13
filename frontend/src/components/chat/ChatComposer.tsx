"use client";

import { useEffect, useRef, useState } from "react";

type ChatComposerProps = {
  onSend: (value: string) => void;
};

export function ChatComposer({ onSend }: ChatComposerProps) {
  const [value, setValue] = useState("");
  const ref = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    const next = Math.min(el.scrollHeight, 140);
    el.style.height = `${next}px`;
  }, [value]);

  const send = () => {
    if (!value.trim()) return;
    onSend(value.trim());
    setValue("");
  };

  return (
    <div className="sticky bottom-0 w-full bg-bg" style={{ paddingBottom: "env(safe-area-inset-bottom)" }}>
      <div className="flex items-end gap-sp2 border-t-soft bg-surface px-pagePad py-sp2">
        <button className="h-btnH w-btnH rounded-r1 border-soft bg-surface text-fs1 text-icon">🎤</button>
        <div className="flex-1 rounded-r1 border-soft bg-surface px-cardPad py-sp2">
          <textarea
            ref={ref}
            rows={1}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
            placeholder="Mesaj yaz"
            className="w-full resize-none bg-transparent text-fs1 text-text placeholder:text-muted focus:outline-none"
            style={{ maxHeight: 140 }}
          />
        </div>
        <button
          onClick={send}
          disabled={!value.trim()}
          className={`h-btnH w-btnH rounded-r1 text-fs1 ${
            value.trim() ? "bg-accent text-bg" : "bg-surface2 text-muted"
          }`}
        >
          ➤
        </button>
      </div>
    </div>
  );
}
