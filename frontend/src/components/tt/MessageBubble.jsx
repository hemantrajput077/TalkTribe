export default function MessageBubble({ message }) {
  const mine = message.from === "me";
  return (
    <div className={`flex ${mine ? "justify-end" : "justify-start"} animate-in fade-in slide-in-from-bottom-1`}>
      <div
        className={`max-w-[78%] rounded-2xl px-4 py-2.5 text-sm shadow-soft ${mine ? "rounded-br-md bg-primary text-primary-foreground" : "rounded-bl-md bg-card text-foreground"}`}
      >
        <p className="leading-relaxed">{message.text}</p>
        <p className={`mt-1 text-right text-[10px] ${mine ? "text-primary-foreground/70" : "text-muted-foreground"}`}>{message.time}</p>
      </div>
    </div>
  );
}
