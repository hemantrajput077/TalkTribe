import { Link } from "@tanstack/react-router";

const base =
  "inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:opacity-50 disabled:pointer-events-none active:scale-[0.98]";

const variants = {
  primary: "bg-primary text-primary-foreground shadow-soft hover:brightness-110 hover:shadow-lift",
  secondary: "bg-primary-soft text-primary hover:bg-secondary",
  outline: "border border-input bg-card text-foreground hover:border-primary hover:text-primary",
  ghost: "text-muted-foreground hover:bg-muted hover:text-foreground",
  danger: "bg-destructive text-destructive-foreground hover:brightness-110",
  "danger-outline": "border border-input bg-card text-destructive hover:border-destructive",
};

const sizes = {
  sm: "h-9 px-3.5 text-sm",
  md: "h-11 px-5 text-sm",
  lg: "h-13 px-7 text-base",
  icon: "h-10 w-10",
};

export function buttonClass({ variant = "primary", size = "md", className = "" } = {}) {
  return `${base} ${variants[variant]} ${sizes[size]} ${className}`;
}

export default function Button({ variant, size, className, to, params, children, ...props }) {
  const cls = buttonClass({ variant, size, className });
  if (to) {
    return (
      <Link to={to} params={params} className={cls} {...props}>
        {children}
      </Link>
    );
  }
  return (
    <button className={cls} {...props}>
      {children}
    </button>
  );
}
