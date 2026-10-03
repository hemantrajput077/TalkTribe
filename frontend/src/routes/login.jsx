import { createFileRoute } from "@tanstack/react-router";
import { LoginPage } from "@/pages/AuthPages";
import { seo } from "@/lib/seo";

export const Route = createFileRoute("/login")({
  head: () => seo("Log in", "Log in to TalkTribe and keep practicing."),
  component: LoginPage,
});
