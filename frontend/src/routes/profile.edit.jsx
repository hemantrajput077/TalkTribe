import { createFileRoute } from "@tanstack/react-router";
import { EditProfilePage } from "@/pages/ProfilePages";
import { seo } from "@/lib/seo";

export const Route = createFileRoute("/profile/edit")({
  head: () => seo("Edit profile", "Update your TalkTribe profile."),
  component: EditProfilePage,
});
