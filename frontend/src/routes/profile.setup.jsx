import { createFileRoute } from "@tanstack/react-router";
import { ProfileSetupPage } from "@/pages/OnboardingPages";
import { seo } from "@/lib/seo";

export const Route = createFileRoute("/profile/setup")({
  head: () => seo("Set up profile", "Tell partners about yourself and your languages."),
  component: ProfileSetupPage,
});
