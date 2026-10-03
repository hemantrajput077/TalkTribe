import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "@tanstack/react-router";
import { Mail, Lock, User, ArrowLeft } from "lucide-react";
import AuthLayout from "@/layouts/AuthLayout";
import Input from "@/components/tt/Input";
import Button from "@/components/tt/Button";
import { useUser } from "@/context/UserContext";

export function LoginPage() {
  const navigate = useNavigate();
  const { login } = useUser();
  const submit = (e) => {
    e.preventDefault();
    login();
    navigate({ to: "/dashboard" });
  };
  return (
    <AuthLayout
      title="Welcome back"
      subtitle="Log in to keep practicing with your partners."
      footer={<>New to TalkTribe? <Link to="/register" className="font-semibold text-primary hover:underline">Create an account</Link></>}
    >
      <form onSubmit={submit} className="space-y-4">
        <Input label="Email" type="email" icon={Mail} placeholder="you@example.com" defaultValue="yogesh@talktribe.app" required />
        <Input label="Password" type="password" icon={Lock} placeholder="••••••••" defaultValue="password" required />
        <div className="flex justify-end">
          <a href="#" className="text-sm font-medium text-primary hover:underline">Forgot password?</a>
        </div>
        <Button type="submit" className="w-full">Log in</Button>
      </form>
    </AuthLayout>
  );
}

export function RegisterPage() {
  const navigate = useNavigate();
  const [error, setError] = useState("");
  const submit = (e) => {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    if (f.get("password") !== f.get("confirm")) return setError("Passwords don't match");
    navigate({ to: "/verify-otp" });
  };
  return (
    <AuthLayout
      title="Create your account"
      subtitle="Join learners practicing English every day."
      footer={<>Already have an account? <Link to="/login" className="font-semibold text-primary hover:underline">Login</Link></>}
    >
      <form onSubmit={submit} className="space-y-4">
        <Input label="Name" icon={User} placeholder="Your full name" required />
        <Input label="Email" type="email" icon={Mail} placeholder="you@example.com" required />
        <Input label="Password" name="password" type="password" icon={Lock} placeholder="At least 8 characters" minLength={8} required />
        <Input label="Confirm Password" name="confirm" type="password" icon={Lock} placeholder="Repeat password" required />
        {error && <p className="text-sm text-destructive" role="alert">{error}</p>}
        <Button type="submit" className="w-full">Create Account</Button>
      </form>
    </AuthLayout>
  );
}

export function OtpPage() {
  const navigate = useNavigate();
  const [digits, setDigits] = useState(Array(6).fill(""));
  const [seconds, setSeconds] = useState(30);
  const refs = useRef([]);

  useEffect(() => {
    if (seconds <= 0) return;
    const t = setTimeout(() => setSeconds((s) => s - 1), 1000);
    return () => clearTimeout(t);
  }, [seconds]);

  const setAt = (i, v) => {
    const val = v.replace(/\D/g, "").slice(-1);
    const next = [...digits];
    next[i] = val;
    setDigits(next);
    if (val && i < 5) refs.current[i + 1]?.focus();
  };
  const onKey = (i, e) => {
    if (e.key === "Backspace" && !digits[i] && i > 0) refs.current[i - 1]?.focus();
  };
  const onPaste = (e) => {
    const p = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6);
    if (!p) return;
    e.preventDefault();
    setDigits(p.padEnd(6, " ").split("").map((c) => c.trim()));
    refs.current[Math.min(p.length, 5)]?.focus();
  };
  const complete = digits.every(Boolean);

  return (
    <AuthLayout title="Verify your email" subtitle="We sent a 6-digit code to your email. Enter it below.">
      <Link to="/register" className="mb-5 -mt-2 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-4 w-4" /> Back
      </Link>
      <form onSubmit={(e) => { e.preventDefault(); navigate({ to: "/profile/setup" }); }}>
        <div className="flex justify-between gap-2" onPaste={onPaste}>
          {digits.map((d, i) => (
            <input
              key={i}
              ref={(el) => (refs.current[i] = el)}
              value={d}
              onChange={(e) => setAt(i, e.target.value)}
              onKeyDown={(e) => onKey(i, e)}
              inputMode="numeric"
              maxLength={1}
              aria-label={`Digit ${i + 1}`}
              className="h-14 w-full rounded-xl border border-input bg-card text-center font-display text-2xl font-bold transition focus:border-primary focus:outline-none focus:ring-4 focus:ring-primary/15"
            />
          ))}
        </div>
        <Button type="submit" className="mt-6 w-full" disabled={!complete}>Verify</Button>
      </form>
      <p className="mt-5 text-center text-sm text-muted-foreground">
        {seconds > 0 ? (
          <>Resend code in <span className="font-semibold text-foreground tabular-nums">0:{String(seconds).padStart(2, "0")}</span></>
        ) : (
          <>Didn't get it? <button onClick={() => setSeconds(30)} className="font-semibold text-primary hover:underline">Resend OTP</button></>
        )}
      </p>
    </AuthLayout>
  );
}
