import Avatar from "./Avatar";

// Large header card used on profile pages.
export default function ProfileCard({ person, children, badge }) {
  return (
    <section className="card-surface overflow-hidden">
      <div className="h-28 bg-primary-soft hero-glow sm:h-36" />
      <div className="px-6 pb-6">
        <div className="-mt-14 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
            <Avatar name={person.name} size="xl" className="rounded-full ring-4 ring-card" />
            <div className="pb-1">
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold sm:text-3xl">{person.name}</h1>
                {badge}
              </div>
              <p className="text-muted-foreground">{person.profession}{person.location ? ` · ${person.location}` : ""}</p>
            </div>
          </div>
          {children && <div className="flex flex-wrap gap-2">{children}</div>}
        </div>
        {person.bio && <p className="mt-5 max-w-2xl leading-relaxed text-foreground/80">{person.bio}</p>}
      </div>
    </section>
  );
}

export function InfoTile({ label, value }) {
  return (
    <div className="rounded-xl bg-muted px-4 py-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-0.5 font-semibold">{value}</p>
    </div>
  );
}
