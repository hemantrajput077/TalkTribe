import { createFileRoute } from "@tanstack/react-router";
import { ProfilePage } from "@/pages/ProfilePages";
import { seo } from "@/lib/seo";

export const Route = createFileRoute("/profile/")({
  head: () => seo("Your profile", "Your TalkTribe profile, languages and interests."),
  component: ProfilePage,
});
