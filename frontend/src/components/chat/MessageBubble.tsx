type MessageBubbleProps = {
  role: "user" | "assistant";
  content: string;
};

export function MessageBubble({ role, content }: MessageBubbleProps) {
  const isUser = role === "user";
  return (
    <div className={`flex w-full ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-full rounded-r2 px-cardPad py-sp2 text-fs1 ${
          isUser ? "bg-accentWeak text-text" : "bg-surface2 text-text"
        }`}
      >
        {content}
      </div>
    </div>
  );
}
