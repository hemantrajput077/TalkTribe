import { createFileRoute } from "@tanstack/react-router";
import { InterestsPage } from "@/pages/OnboardingPages";
import { seo } from "@/lib/seo";

export const Route = createFileRoute("/interests")({
  head: () => seo("Choose interests", "Pick topics you love talking about."),
  component: InterestsPage,
});
