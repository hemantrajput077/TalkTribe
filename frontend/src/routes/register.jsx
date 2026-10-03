import { createFileRoute } from "@tanstack/react-router";
import { RegisterPage } from "@/pages/AuthPages";
import { seo } from "@/lib/seo";

export const Route = createFileRoute("/register")({
  head: () => seo("Create account", "Join TalkTribe and start practicing English."),
  component: RegisterPage,
});
