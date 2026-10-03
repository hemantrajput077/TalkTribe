import { useState } from "react";
import { SendHorizontal } from "lucide-react";

export default function ChatInput({ onSend }) {
  const [text, setText] = useState("");
  const submit = (e) => {
    e.preventDefault();
    if (!text.trim()) return;
    onSend(text.trim());
    setText("");
  };
  return (
    <form onSubmit={submit} className="flex items-center gap-2 border-t bg-card p-3">
      <input
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Type a message..."
        aria-label="Message"
        className="flex-1 rounded-xl bg-muted px-4 py-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
      />
      <button
        type="submit"
        disabled={!text.trim()}
        aria-label="Send"
        className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary text-primary-foreground transition hover:brightness-110 disabled:opacity-40"
      >
        <SendHorizontal className="h-5 w-5" />
      </button>
    </form>
  );
}
