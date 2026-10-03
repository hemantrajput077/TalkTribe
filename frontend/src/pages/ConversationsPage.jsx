import { useEffect, useRef, useState } from "react";
import { ArrowLeft, MessageCircle, Phone, Video } from "lucide-react";
import { Link } from "@tanstack/react-router";
import Navbar, { MobileNav } from "@/components/tt/Navbar";
import ConversationList from "@/components/tt/ConversationList";
import MessageBubble from "@/components/tt/MessageBubble";
import ChatInput from "@/components/tt/ChatInput";
import Avatar from "@/components/tt/Avatar";
import { EmptyState, LoadingState } from "@/components/tt/States";
import { useAsync } from "@/hooks/useAsync";
import { getConversations, getMessages } from "@/services/api";

function now() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: false });
}

export default function ConversationsPage() {
  const { data: conversations, loading } = useAsync(getConversations);
  const [activeId, setActiveId] = useState(null);
  const [query, setQuery] = useState("");
  const [threads, setThreads] = useState({});
  const endRef = useRef(null);

  useEffect(() => {
    if (!activeId || threads[activeId]) return;
    getMessages(activeId).then((msgs) => setThreads((t) => ({ ...t, [activeId]: msgs })));
  }, [activeId, threads]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [threads, activeId]);

  const active = conversations?.find((c) => c.id === activeId);
  const messages = threads[activeId];
  const send = (text) =>
    setThreads((t) => ({ ...t, [activeId]: [...(t[activeId] || []), { id: crypto.randomUUID(), from: "me", text, time: now() }] }));

  return (
    <div className="flex h-dvh flex-col">
      <Navbar />
      <div className="mx-auto flex min-h-0 w-full max-w-6xl flex-1 pb-16 md:p-6">
        <div className="card-surface flex min-h-0 flex-1 overflow-hidden max-md:rounded-none max-md:border-0">
          <aside className={`w-full border-r md:w-80 ${activeId ? "hidden md:block" : "block"}`}>
            {loading ? <LoadingState /> : <ConversationList conversations={conversations} activeId={activeId} onSelect={setActiveId} query={query} onQuery={setQuery} />}
          </aside>

          <section className={`min-w-0 flex-1 flex-col bg-muted ${activeId ? "flex" : "hidden md:flex"}`}>
            {!active ? (
              <div className="flex flex-1 items-center justify-center">
                <EmptyState icon={MessageCircle} title="Pick a conversation" description="Select a chat on the left, or find a new partner to practice with." />
              </div>
            ) : (
              <>
                <header className="flex items-center gap-3 border-b bg-card px-4 py-3">
                  <button className="rounded-lg p-1.5 hover:bg-muted md:hidden" onClick={() => setActiveId(null)} aria-label="Back to conversations">
                    <ArrowLeft className="h-5 w-5" />
                  </button>
                  <Link to="/partners/$id" params={{ id: active.partner.id }} className="flex min-w-0 flex-1 items-center gap-3">
                    <Avatar name={active.partner.name} online={active.partner.online} />
                    <div className="min-w-0">
                      <p className="truncate font-semibold">{active.partner.name}</p>
                      <p className="text-xs text-muted-foreground">{active.partner.online ? "Online" : "Last seen recently"}</p>
                    </div>
                  </Link>
                  <Link to="/call/$id" params={{ id: active.partner.id }} search={{ mode: "audio" }} aria-label="Voice call" className="rounded-xl p-2.5 text-muted-foreground hover:bg-muted hover:text-primary"><Phone className="h-5 w-5" /></Link>
                  <Link to="/call/$id" params={{ id: active.partner.id }} aria-label="Video call" className="rounded-xl p-2.5 text-muted-foreground hover:bg-muted hover:text-primary"><Video className="h-5 w-5" /></Link>
                </header>
                <div className="flex-1 space-y-3 overflow-y-auto p-4 sm:p-6">
                  {!messages ? (
                    <LoadingState />
                  ) : messages.length === 0 ? (
                    <EmptyState icon={MessageCircle} title="Say hello 👋" description={`Start your first conversation with ${active.partner.name.split(" ")[0]}.`} />
                  ) : (
                    messages.map((m) => <MessageBubble key={m.id} message={m} />)
                  )}
                  <div ref={endRef} />
                </div>
                <ChatInput onSend={send} />
              </>
            )}
          </section>
        </div>
      </div>
      <MobileNav />
    </div>
  );
}
