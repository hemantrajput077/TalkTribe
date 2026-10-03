import { createFileRoute } from "@tanstack/react-router";
import LandingPage from "@/pages/LandingPage";
import { seo } from "@/lib/seo";

export const Route = createFileRoute("/")({
  head: () => seo("Practice languages, meet people", "Find language partners and build English confidence through real conversations."),
  component: LandingPage,
});
