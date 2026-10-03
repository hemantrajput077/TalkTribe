import { createFileRoute } from "@tanstack/react-router";
import CallPage from "@/pages/CallPage";
import { seo } from "@/lib/seo";

export const Route = createFileRoute("/call/$id")({
  head: () => seo("Call", "Voice and video practice call."),
  component: RouteComponent,
});

function RouteComponent() {
  const { id } = Route.useParams();
  return <CallPage id={id} />;
}
