import { Link } from "@tanstack/react-router";
import { MessagesSquare } from "lucide-react";

export default function Logo({ to = "/" }) {
  return (
    <Link to={to} className="flex items-center gap-2" aria-label="TalkTribe home">
      <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary text-primary-foreground">
        <MessagesSquare className="h-5 w-5" />
      </span>
      <span className="font-display text-xl font-bold tracking-tight">TalkTribe</span>
    </Link>
  );
}
