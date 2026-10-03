import Button from "./Button";

export default function ProgressCard({ value }) {
  const r = 34;
  const c = 2 * Math.PI * r;
  return (
    <div className="card-surface flex items-center gap-5 p-5">
      <svg width="84" height="84" viewBox="0 0 84 84" className="shrink-0 -rotate-90" aria-hidden="true">
        <circle cx="42" cy="42" r={r} strokeWidth="8" className="fill-none stroke-muted" />
        <circle cx="42" cy="42" r={r} strokeWidth="8" strokeLinecap="round" strokeDasharray={c} strokeDashoffset={c - (c * value) / 100} className="fill-none stroke-primary transition-all duration-700" />
      </svg>
      <div>
        <p className="text-sm text-muted-foreground">Profile completion</p>
        <p className="font-display text-3xl font-bold">{value}%</p>
        <Button to="/profile/edit" variant="secondary" size="sm" className="mt-2">
          Complete your profile
        </Button>
      </div>
    </div>
  );
}
