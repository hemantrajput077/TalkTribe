import { createFileRoute } from "@tanstack/react-router";
import PartnerProfilePage from "@/pages/PartnerProfilePage";
import { seo } from "@/lib/seo";

export const Route = createFileRoute("/partners/$id")({
  head: () => seo("Partner profile", "View a language partner's profile."),
  component: RouteComponent,
});

function RouteComponent() {
  const { id } = Route.useParams();
  return <PartnerProfilePage id={id} />;
}
