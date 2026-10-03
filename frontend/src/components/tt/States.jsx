import { Loader2 } from "lucide-react";

export function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center px-6 py-16 text-center">
      {Icon && (
        <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary-soft text-primary">
          <Icon className="h-6 w-6" />
        </div>
      )}
      <h3 className="text-lg font-bold">{title}</h3>
      {description && <p className="mt-1 max-w-xs text-sm text-muted-foreground">{description}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

export function LoadingState({ label = "Loading…" }) {
  return (
    <div className="flex items-center justify-center gap-2 py-16 text-sm text-muted-foreground">
      <Loader2 className="h-4 w-4 animate-spin" /> {label}
    </div>
  );
}

export function CardSkeleton() {
  return (
    <div className="card-surface animate-pulse p-5">
      <div className="flex gap-3">
        <div className="h-12 w-12 rounded-full bg-muted" />
        <div className="flex-1 space-y-2 pt-1">
          <div className="h-3 w-2/3 rounded bg-muted" />
          <div className="h-3 w-1/3 rounded bg-muted" />
        </div>
      </div>
      <div className="mt-5 h-12 rounded-lg bg-muted" />
      <div className="mt-3 h-3 rounded bg-muted" />
      <div className="mt-2 h-3 w-4/5 rounded bg-muted" />
      <div className="mt-5 h-9 rounded-xl bg-muted" />
    </div>
  );
}
