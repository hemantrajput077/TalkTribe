import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "@tanstack/react-router";
import { Mail, Lock, User, Phone, AtSign, ArrowLeft, Loader2 } from "lucide-react";
import AuthLayout from "@/layouts/AuthLayout";
import Input from "@/components/tt/Input";
import Button from "@/components/tt/Button";
import { useUser } from "@/context/UserContext";
import { register, verifyEmail, resendOtp } from "@/services/api";

// ─── Login ─────────────────────────────────────────────────────────────────
export function LoginPage() {
  const navigate = useNavigate();
  const { login } = useUser();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    const f = new FormData(e.currentTarget);
    const username = f.get("username");
    const password = f.get("password");
    try {
      await login(username, password);
      navigate({ to: "/dashboard" });
    } catch (err) {
      setError(err.message || "Login failed. Check your username and password.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout
      title="Welcome back"
      subtitle="Log in to keep practicing with your partners."
      footer={<>New to TalkTribe? <Link to="/register" className="font-semibold text-primary hover:underline">Create an account</Link></>}
    >
      <form onSubmit={submit} className="space-y-4">
        <Input
          name="username"
          label="Username"
          type="text"
          icon={AtSign}
          placeholder="your_username"
          required
          autoComplete="username"
        />
        <Input
          name="password"
          label="Password"
          type="password"
          icon={Lock}
          placeholder="••••••••"
          required
          autoComplete="current-password"
        />
        <div className="flex justify-end">
          <a href="#" className="text-sm font-medium text-primary hover:underline">Forgot password?</a>
        </div>
        {error && <p className="text-sm text-destructive" role="alert">{error}</p>}
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Logging in…</> : "Log in"}
        </Button>
      </form>
    </AuthLayout>
  );
}

// ─── Register ───────────────────────────────────────────────────────────────
export function RegisterPage() {
  const navigate = useNavigate();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    const f = new FormData(e.currentTarget);
    const password = f.get("password");
    const confirm = f.get("confirm");
    if (password !== confirm) return setError("Passwords don't match.");

    const payload = {
      username: f.get("username"),
      email: f.get("email"),
      phone_number: f.get("phone_number"),
      password,
      full_name: f.get("full_name") || undefined,
    };

    setLoading(true);
    try {
      await register(payload);
      // Pass email via sessionStorage so OTP page knows where to send
      sessionStorage.setItem("otp_email", payload.email);
      navigate({ to: "/verify-otp" });
    } catch (err) {
      setError(err.message || "Registration failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout
      title="Create your account"
      subtitle="Join learners practicing English every day."
      footer={<>Already have an account? <Link to="/login" className="font-semibold text-primary hover:underline">Login</Link></>}
    >
      <form onSubmit={submit} className="space-y-4">
        <Input name="username" label="Username" icon={AtSign} placeholder="cool_username" minLength={3} maxLength={30} pattern="[a-zA-Z0-9_]+" title="Letters, numbers and underscores only" required />
        <Input name="email" label="Email" type="email" icon={Mail} placeholder="you@example.com" required />
        <Input name="phone_number" label="Phone Number" icon={Phone} placeholder="+919876543210" required title="E.164 format e.g. +919876543210" />
        <Input name="password" label="Password" type="password" icon={Lock} placeholder="Min 8 chars, uppercase, number, symbol" minLength={8} required autoComplete="new-password" />
        <Input name="confirm" label="Confirm Password" type="password" icon={Lock} placeholder="Min 8 chars, uppercase, number, symbol" minLength={8} required autoComplete="new-password" />
        <Input name="full_name" label="Full Name" icon={User} placeholder="Your full name" />
        {error && <p className="text-sm text-destructive" role="alert">{error}</p>}
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Creating account…</> : "Create Account"}
        </Button>
      </form>
    </AuthLayout>
  );
}

// ─── OTP Verification ────────────────────────────────────────────────────────
export function OtpPage() {
  const navigate = useNavigate();
  const [digits, setDigits] = useState(Array(6).fill(""));
  const [seconds, setSeconds] = useState(60);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const refs = useRef([]);

  const email = sessionStorage.getItem("otp_email") || "";

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

  const handleVerify = async (e) => {
    e.preventDefault();
    if (!complete) return;
    setError("");
    setLoading(true);
    try {
      const otp = digits.join("");
      await verifyEmail(email, otp);
      sessionStorage.removeItem("otp_email");
      // After verification user must log in to get tokens
      navigate({ to: "/login" });
    } catch (err) {
      setError(err.message || "Invalid OTP. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setError("");
    setResending(true);
    try {
      await resendOtp(email);
      setSeconds(60);
      setDigits(Array(6).fill(""));
      refs.current[0]?.focus();
    } catch (err) {
      setError(err.message || "Failed to resend OTP.");
    } finally {
      setResending(false);
    }
  };

  return (
    <AuthLayout
      title="Verify your email"
      subtitle={email ? `We sent a 6-digit code to ${email}.` : "Enter the 6-digit code we sent to your email."}
    >
      <Link to="/register" className="mb-5 -mt-2 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-4 w-4" /> Back
      </Link>
      <form onSubmit={handleVerify}>
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
        {error && <p className="mt-3 text-sm text-destructive" role="alert">{error}</p>}
        <Button type="submit" className="mt-6 w-full" disabled={!complete || loading}>
          {loading ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Verifying…</> : "Verify Email"}
        </Button>
      </form>
      <p className="mt-5 text-center text-sm text-muted-foreground">
        {seconds > 0 ? (
          <>Resend code in <span className="font-semibold text-foreground tabular-nums">0:{String(seconds).padStart(2, "0")}</span></>
        ) : (
          <>Didn't get it? <button onClick={handleResend} disabled={resending} className="font-semibold text-primary hover:underline disabled:opacity-50">{resending ? "Sending…" : "Resend OTP"}</button></>
        )}
      </p>
    </AuthLayout>
  );
}
