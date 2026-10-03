import { createFileRoute } from "@tanstack/react-router";
import DashboardPage from "@/pages/DashboardPage";
import { seo } from "@/lib/seo";

export const Route = createFileRoute("/dashboard")({
  head: () => seo("Dashboard", "Your practice hub and suggested partners."),
  component: DashboardPage,
});
