import { ArrowRight, Flame, MessageCircle, Loader2 } from "lucide-react";
import { Link, useNavigate } from "@tanstack/react-router";
import AppLayout from "@/layouts/AppLayout";
import ProgressCard from "@/components/tt/ProgressCard";
import InterestChip from "@/components/tt/InterestChip";
import PartnerCard from "@/components/tt/PartnerCard";
import { CardSkeleton } from "@/components/tt/States";
import { useUser } from "@/context/UserContext";
import { useAsync } from "@/hooks/useAsync";
import { getPartners } from "@/services/api";

function greeting() {
  const h = new Date().getHours();
  return h < 12 ? "Good morning" : h < 18 ? "Good afternoon" : "Good evening";
}

export default function DashboardPage() {
  const { user, loading } = useUser();
  const navigate = useNavigate();
  // ⚠️ Hooks MUST be called before any early return (React Rules of Hooks)
  const { data: partners, loading: partnersLoading } = useAsync(getPartners);

  // While the user profile is being fetched, show a spinner
  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="animate-spin h-8 w-8 text-primary" />
      </div>
    );
  }

  // If no user after loading, redirect to login
  if (!user) {
    navigate({ to: "/login" });
    return null;
  }

  // Backend returns full_name, mock data uses name — handle both
  const displayName = user.full_name || user.name || user.username || "User";
  const firstName = displayName.split(" ")[0];
  const interests = user.interests || [];
  const profileCompletion = user.profileCompletion ?? 50;

  return (
    <AppLayout>
      <section className="grid gap-5 lg:grid-cols-3">
        <div className="card-surface hero-glow flex flex-col justify-between p-6 lg:col-span-2">
          <div>
            <h1 className="text-3xl font-bold sm:text-4xl">{greeting()}, {firstName} 👋</h1>
            <p className="mt-2 text-muted-foreground">Ready to practice English today?</p>
          </div>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link to="/conversations" className="inline-flex items-center gap-2 rounded-xl bg-card px-4 py-2.5 text-sm font-semibold shadow-soft hover:text-primary">
              <MessageCircle className="h-4 w-4" /> 3 unread messages
            </Link>
            <span className="inline-flex items-center gap-2 rounded-xl bg-card px-4 py-2.5 text-sm font-semibold shadow-soft">
              <Flame className="h-4 w-4 text-warm" /> 5-day streak
            </span>
          </div>
        </div>
        <ProgressCard value={profileCompletion} />
      </section>

      {interests.length > 0 && (
        <section className="mt-8">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold">Your interests</h2>
            <Link to="/interests" className="text-sm font-medium text-primary hover:underline">Edit</Link>
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            {interests.map((i) => <InterestChip key={i} label={i} />)}
          </div>
        </section>
      )}

      <section className="mt-10">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold">Suggested partners</h2>
          <Link to="/partners" className="inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline">See all <ArrowRight className="h-4 w-4" /></Link>
        </div>
        <div className="mt-4 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {partnersLoading
            ? Array.from({ length: 3 }).map((_, i) => <CardSkeleton key={i} />)
            : (partners || []).slice(0, 3).map((p) => <PartnerCard key={p.id} partner={p} myInterests={interests} />)}
        </div>
      </section>
    </AppLayout>
  );
}
