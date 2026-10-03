import { createFileRoute } from "@tanstack/react-router";
import { OtpPage } from "@/pages/AuthPages";
import { seo } from "@/lib/seo";

export const Route = createFileRoute("/verify-otp")({
  head: () => seo("Verify email", "Enter your 6-digit verification code."),
  component: OtpPage,
});
