import { Check } from "lucide-react";

export default function InterestChip({ label, selected, shared, onClick, size = "md" }) {
  const pad = size === "sm" ? "px-2.5 py-1 text-xs" : "px-4 py-2 text-sm";
  const state = selected
    ? "bg-primary text-primary-foreground border-primary"
    : shared
      ? "bg-accent text-accent-foreground border-transparent"
      : "bg-card text-foreground border-border";
  const Tag = onClick ? "button" : "span";
  return (
    <Tag
      type={onClick ? "button" : undefined}
      onClick={onClick}
      aria-pressed={onClick ? !!selected : undefined}
      className={`inline-flex items-center gap-1.5 rounded-full border font-medium transition ${pad} ${state} ${onClick ? "hover:border-primary cursor-pointer" : ""}`}
    >
      {selected && <Check className="h-3.5 w-3.5" />}
      {label}
    </Tag>
  );
}
