import { Link, useNavigate } from "@tanstack/react-router";
import { Home, Users, MessageCircle, User, LogOut } from "lucide-react";
import Logo from "./Logo";
import Avatar from "./Avatar";
import { useUser } from "@/context/UserContext";

export const NAV_ITEMS = [
  { to: "/dashboard", label: "Home", icon: Home },
  { to: "/partners", label: "Find Partners", icon: Users },
  { to: "/conversations", label: "Conversations", icon: MessageCircle },
  { to: "/profile", label: "Profile", icon: User },
];

const linkCls = "flex items-center gap-2 rounded-xl px-3.5 py-2 text-sm font-medium text-muted-foreground transition hover:bg-muted hover:text-foreground";
const activeCls = "bg-primary-soft text-primary hover:bg-primary-soft hover:text-primary";

export default function Navbar() {
  const { user, logout } = useUser();
  const navigate = useNavigate();
  const handleLogout = () => {
    logout();
    navigate({ to: "/login" });
  };
  return (
    <header className="sticky top-0 z-40 border-b bg-card/85 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <Logo to="/dashboard" />
        <nav className="hidden items-center gap-1 md:flex" aria-label="Main">
          {NAV_ITEMS.slice(1).map(({ to, label, icon: Icon }) => (
            <Link key={to} to={to} className={linkCls} activeProps={{ className: activeCls }}>
              <Icon className="h-4 w-4" /> {label}
            </Link>
          ))}
        </nav>
        <div className="flex items-center gap-2">
          {user ? (
            <>
              <Link to="/profile" aria-label="Your profile">
                <Avatar name={user.full_name || user.name || user.username || "User"} size="sm" />
              </Link>
              <button onClick={handleLogout} className={`${linkCls} px-2.5`} aria-label="Logout">
                <LogOut className="h-4 w-4" />
                <span className="hidden lg:inline">Logout</span>
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className={linkCls}>Log in</Link>
              <Link to="/register" className={`${linkCls} bg-primary text-white hover:bg-primary/90 hover:text-white`}>Sign up</Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
}

export function MobileNav() {
  return (
    <nav aria-label="Mobile" className="fixed inset-x-0 bottom-0 z-40 border-t bg-card/95 backdrop-blur md:hidden">
      <div className="grid grid-cols-4">
        {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
          <Link
            key={to}
            to={to}
            className="flex flex-col items-center gap-1 py-2.5 text-[11px] font-medium text-muted-foreground"
            activeProps={{ className: "text-primary" }}
          >
            <Icon className="h-5 w-5" />
            {label.replace("Find ", "")}
          </Link>
        ))}
      </div>
    </nav>
  );
}
