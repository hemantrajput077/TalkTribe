import { createFileRoute } from "@tanstack/react-router";
import PartnersPage from "@/pages/PartnersPage";
import { seo } from "@/lib/seo";

export const Route = createFileRoute("/partners/")({
  head: () => seo("Find partners", "Discover language partners who share your interests."),
  component: PartnersPage,
});
