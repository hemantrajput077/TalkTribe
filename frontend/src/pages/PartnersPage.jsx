import { useMemo, useState } from "react";
import { Search, SlidersHorizontal, UserX, X } from "lucide-react";
import AppLayout from "@/layouts/AppLayout";
import PartnerCard from "@/components/tt/PartnerCard";
import InterestChip from "@/components/tt/InterestChip";
import Button from "@/components/tt/Button";
import { Select } from "@/components/tt/Input";
import { CardSkeleton, EmptyState } from "@/components/tt/States";
import { useUser } from "@/context/UserContext";
import { useAsync } from "@/hooks/useAsync";
import { getPartners } from "@/services/api";
import { PROFICIENCY_LEVELS, PROFESSIONS } from "@/data/mockData";
import { getInterests } from "@/services/api";

export default function PartnersPage() {
  const { user } = useUser();
  const { data: partners, loading } = useAsync(getPartners);
  const { data: allInterests, loading: interestsLoading } = useAsync(getInterests);
  const [query, setQuery] = useState("");
  const [showFilters, setShowFilters] = useState(false);
  const [selectedInterests, setSelectedInterests] = useState([]);
  const [level, setLevel] = useState("Any level");
  const [profession, setProfession] = useState("Any profession");

  // Local UI filtering on mock data. Later these values become query params for the API.
  const results = useMemo(() => {
    if (!partners) return [];
    return partners.filter(
      (p) =>
        (p.name + p.profession + p.nativeLanguage).toLowerCase().includes(query.toLowerCase()) &&
        (selectedInterests.length === 0 || selectedInterests.some((i) => p.interests.includes(i))) &&
        (level === "Any level" || p.englishLevel === level) &&
        (profession === "Any profession" || p.profession === profession),
    );
  }, [partners, query, selectedInterests, level, profession]);

  const activeCount = selectedInterests.length + (level !== "Any level") + (profession !== "Any profession");
  const clear = () => { setSelectedInterests([]); setLevel("Any level"); setProfession("Any profession"); setQuery(""); };
  const toggle = (i) => setSelectedInterests((s) => (s.includes(i) ? s.filter((x) => x !== i) : [...s, i]));

  return (
    <AppLayout>
      <h1 className="text-3xl font-bold sm:text-4xl">Find Language Partners</h1>
      <p className="mt-2 text-muted-foreground">Find people who match your interests and learning goals.</p>

      <div className="mt-6 flex gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by name, profession or language"
            aria-label="Search partners"
            className="h-12 w-full rounded-xl border border-input bg-card pl-11 pr-4 text-sm shadow-soft placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-4 focus:ring-primary/15"
          />
        </div>
        <Button variant={showFilters ? "secondary" : "outline"} className="h-12" onClick={() => setShowFilters((s) => !s)} aria-expanded={showFilters}>
          <SlidersHorizontal className="h-4 w-4" />
          <span className="hidden sm:inline">Filters</span>
          {activeCount > 0 && <span className="rounded-full bg-primary px-1.5 text-[10px] text-primary-foreground">{activeCount}</span>}
        </Button>
      </div>

      {showFilters && (
        <div className="card-surface mt-4 space-y-5 p-5 animate-in fade-in slide-in-from-top-2">
          <div>
            <p className="mb-2 text-sm font-medium">Interests</p>
            <div className="flex flex-wrap gap-2">
              {interestsLoading ? <p>Loading interests…</p> : (allInterests || []).map((i) => <InterestChip key={i} label={i} size="sm" selected={selectedInterests.includes(i)} onClick={() => toggle(i)} />)}
            </div>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <Select label="English proficiency" value={level} onChange={(e) => setLevel(e.target.value)} options={["Any level", ...PROFICIENCY_LEVELS]} />
            <Select label="Profession" value={profession} onChange={(e) => setProfession(e.target.value)} options={["Any profession", ...PROFESSIONS]} />
          </div>
          <div className="flex justify-end">
            <Button variant="ghost" size="sm" onClick={clear}><X className="h-4 w-4" /> Clear all</Button>
          </div>
        </div>
      )}

      {!loading && <p className="mt-6 text-sm text-muted-foreground">{results.length} partners found</p>}

      <div className="mt-3 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {loading
          ? Array.from({ length: 6 }).map((_, i) => <CardSkeleton key={i} />)
          : results.map((p) => <PartnerCard key={p.id} partner={p} myInterests={user.interests} />)}
      </div>
      {!loading && results.length === 0 && (
        <EmptyState icon={UserX} title="No partners match" description="Try removing a filter or searching for something else." action={<Button variant="outline" onClick={clear}>Clear filters</Button>} />
      )}
    </AppLayout>
  );
}
