import { Search } from "lucide-react";
import Avatar from "./Avatar";

export default function ConversationList({ conversations, activeId, onSelect, query, onQuery }) {
  const list = conversations.filter((c) => c.partner.name.toLowerCase().includes(query.toLowerCase()));
  return (
    <div className="flex h-full flex-col">
      <div className="border-b p-4">
        <h2 className="mb-3 text-lg font-bold">Conversations</h2>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            value={query}
            onChange={(e) => onQuery(e.target.value)}
            placeholder="Search conversations"
            aria-label="Search conversations"
            className="w-full rounded-xl bg-muted py-2.5 pl-9 pr-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
      </div>
      <ul className="flex-1 overflow-y-auto p-2">
        {list.map((c) => (
          <li key={c.id}>
            <button
              onClick={() => onSelect(c.id)}
              className={`flex w-full items-center gap-3 rounded-xl p-3 text-left transition ${activeId === c.id ? "bg-primary-soft" : "hover:bg-muted"}`}
            >
              <Avatar name={c.partner.name} online={c.partner.online} />
              <div className="min-w-0 flex-1">
                <div className="flex items-baseline justify-between gap-2">
                  <p className="truncate text-sm font-semibold">{c.partner.name}</p>
                  <span className="shrink-0 text-[11px] text-muted-foreground">{c.time}</span>
                </div>
                <div className="flex items-center justify-between gap-2">
                  <p className="truncate text-xs text-muted-foreground">{c.lastMessage}</p>
                  {c.unread > 0 && (
                    <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-primary px-1.5 text-[10px] font-bold text-primary-foreground">{c.unread}</span>
                  )}
                </div>
              </div>
            </button>
          </li>
        ))}
        {list.length === 0 && <p className="p-6 text-center text-sm text-muted-foreground">No conversations found</p>}
      </ul>
    </div>
  );
}
