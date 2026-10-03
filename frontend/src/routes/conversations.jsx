import { createFileRoute } from "@tanstack/react-router";
import ConversationsPage from "@/pages/ConversationsPage";
import { seo } from "@/lib/seo";

export const Route = createFileRoute("/conversations")({
  head: () => seo("Conversations", "Chat with your language partners."),
  component: ConversationsPage,
});
