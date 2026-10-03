const palette = ["bg-av1", "bg-av2", "bg-av3", "bg-av4", "bg-av5"];
const sizes = {
  sm: "h-9 w-9 text-xs",
  md: "h-12 w-12 text-sm",
  lg: "h-16 w-16 text-lg",
  xl: "h-28 w-28 text-3xl",
};

export default function Avatar({ name = "", src, size = "md", online, className = "" }) {
  const initials = name.split(" ").map((n) => n[0]).slice(0, 2).join("").toUpperCase();
  const color = palette[[...name].reduce((a, c) => a + c.charCodeAt(0), 0) % palette.length];
  return (
    <div className={`relative shrink-0 ${className}`}>
      {src ? (
        <img src={src} alt={name} className={`${sizes[size]} rounded-full object-cover`} />
      ) : (
        <div className={`${sizes[size]} ${color} flex items-center justify-center rounded-full font-bold text-secondary-foreground`}>
          {initials}
        </div>
      )}
      {online !== undefined && (
        <span
          aria-label={online ? "Online" : "Offline"}
          className={`absolute bottom-0 right-0 h-3 w-3 rounded-full border-2 border-card ${online ? "bg-success" : "bg-input"}`}
        />
      )}
    </div>
  );
}
