import { ArrowRight, Flame, MessageCircle } from "lucide-react";
import { Link } from "@tanstack/react-router";
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
  const { user } = useUser();
  const { data: partners, loading } = useAsync(getPartners);
  return (
    <AppLayout>
      <section className="grid gap-5 lg:grid-cols-3">
        <div className="card-surface hero-glow flex flex-col justify-between p-6 lg:col-span-2">
          <div>
            <h1 className="text-3xl font-bold sm:text-4xl">{greeting()}, {user.name.split(" ")[0]} 👋</h1>
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
        <ProgressCard value={user.profileCompletion} />
      </section>

      <section className="mt-8">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold">Your interests</h2>
          <Link to="/interests" className="text-sm font-medium text-primary hover:underline">Edit</Link>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          {user.interests.map((i) => <InterestChip key={i} label={i} />)}
        </div>
      </section>

      <section className="mt-10">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold">Suggested partners</h2>
          <Link to="/partners" className="inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline">See all <ArrowRight className="h-4 w-4" /></Link>
        </div>
        <div className="mt-4 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {loading
            ? Array.from({ length: 3 }).map((_, i) => <CardSkeleton key={i} />)
            : partners.slice(0, 3).map((p) => <PartnerCard key={p.id} partner={p} myInterests={user.interests} />)}
        </div>
      </section>
    </AppLayout>
  );
}
