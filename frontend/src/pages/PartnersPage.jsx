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
import { getPartners, getInterests } from "@/services/api";
import { PROFICIENCY_LEVELS, PROFESSIONS } from "@/data/mockData";

export default function PartnersPage() {
  const { user } = useUser();
  const { data: partners, loading } = useAsync(getPartners);
  const { data: allInterests, loading: interestsLoading } = useAsync(getInterests);
  const [query, setQuery] = useState("");
  const [showFilters, setShowFilters] = useState(false);
  const [selectedInterests, setSelectedInterests] = useState([]);
  const [level, setLevel] = useState("Any level");
  const [profession, setProfession] = useState("Any profession");

  const results = useMemo(() => {
    if (!partners) return [];
    return partners.filter((p) => {
      const pName = p.name || p.display_name || "";
      const pProf = p.profession || "";
      const pLang = p.nativeLanguage || "";
      const pInterests = Array.isArray(p.interests) ? p.interests : (p.shared_interests || []);
      const pLevel = p.englishLevel || p.proficiency_level || "";

      const matchesQuery = (pName + " " + pProf + " " + pLang).toLowerCase().includes(query.toLowerCase());
      const matchesInterests =
        selectedInterests.length === 0 ||
        selectedInterests.some((i) => pInterests.includes(i));
      const matchesLevel = level === "Any level" || pLevel === level;
      const matchesProf = profession === "Any profession" || pProf === profession;

      return matchesQuery && matchesInterests && matchesLevel && matchesProf;
    });
  }, [partners, query, selectedInterests, level, profession]);

  const activeCount = selectedInterests.length + (level !== "Any level" ? 1 : 0) + (profession !== "Any profession" ? 1 : 0);
  const clear = () => {
    setSelectedInterests([]);
    setLevel("Any level");
    setProfession("Any profession");
    setQuery("");
  };

  const toggle = (label) =>
    setSelectedInterests((s) => (s.includes(label) ? s.filter((x) => x !== label) : [...s, label]));

  const myInterestsList = Array.isArray(user?.interests) ? user.interests : [];

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
        <Button
          variant={showFilters ? "secondary" : "outline"}
          className="h-12"
          onClick={() => setShowFilters((s) => !s)}
          aria-expanded={showFilters}
        >
          <SlidersHorizontal className="h-4 w-4" />
          <span className="hidden sm:inline">Filters</span>
          {activeCount > 0 && (
            <span className="rounded-full bg-primary px-1.5 text-[10px] text-primary-foreground">{activeCount}</span>
          )}
        </Button>
      </div>

      {showFilters && (
        <div className="card-surface mt-4 space-y-5 p-5 animate-in fade-in slide-in-from-top-2">
          <div>
            <p className="mb-2 text-sm font-medium">Interests</p>
            <div className="flex flex-wrap gap-2">
              {interestsLoading ? (
                <p className="text-sm text-muted-foreground">Loading interests…</p>
              ) : (
                (allInterests || []).map((i) => {
                  const label = typeof i === "object" ? i.name : i;
                  return (
                    <InterestChip
                      key={typeof i === "object" ? i.id || i.name : i}
                      label={label}
                      size="sm"
                      selected={selectedInterests.includes(label)}
                      onClick={() => toggle(label)}
                    />
                  );
                })
              )}
            </div>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <Select
              label="English proficiency"
              value={level}
              onChange={(e) => setLevel(e.target.value)}
              options={["Any level", ...PROFICIENCY_LEVELS]}
            />
            <Select
              label="Profession"
              value={profession}
              onChange={(e) => setProfession(e.target.value)}
              options={["Any profession", ...PROFESSIONS]}
            />
          </div>
          <div className="flex justify-end">
            <Button variant="ghost" size="sm" onClick={clear}>
              <X className="h-4 w-4" /> Clear all
            </Button>
          </div>
        </div>
      )}

      {!loading && <p className="mt-6 text-sm text-muted-foreground">{results.length} partners found</p>}

      <div className="mt-3 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {loading
          ? Array.from({ length: 6 }).map((_, i) => <CardSkeleton key={i} />)
          : results.map((p) => (
              <PartnerCard key={p.id} partner={p} myInterests={myInterestsList} />
            ))}
      </div>

      {!loading && results.length === 0 && (
        <EmptyState
          icon={UserX}
          title="No partners match"
          description="Try removing a filter or searching for something else."
          action={<Button variant="outline" onClick={clear}>Clear filters</Button>}
        />
      )}
    </AppLayout>
  );
}
