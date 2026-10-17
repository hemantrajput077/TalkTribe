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
    const username = f.get("username")?.toString().trim() || "";
    const password = f.get("password")?.toString() || "";

    try {
      await login(username, password);
      navigate({ to: "/dashboard" });
    } catch (err) {
      const msg = err.message || "";
      if (msg.includes("EMAIL_NOT_VERIFIED")) {
        setError("Your email is not verified yet. Please verify your OTP to continue.");
      } else if (msg.includes("Incorrect username or password")) {
        setError("Incorrect username/email or password.");
      } else {
        setError(msg || "Login failed. Check your credentials.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout
      title="Welcome back"
      subtitle="Log in to keep practicing with your partners."
      footer={
        <>
          New to TalkTribe?{" "}
          <Link to="/register" className="font-semibold text-primary hover:underline">
            Create an account
          </Link>
        </>
      }
    >
      <form onSubmit={submit} className="space-y-4">
        <Input
          name="username"
          label="Username or Email"
          type="text"
          icon={AtSign}
          placeholder="your_username or you@example.com"
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
        <div className="flex justify-between items-center text-sm">
          <Link to="/verify-otp" className="font-medium text-muted-foreground hover:text-foreground">
            Verify OTP?
          </Link>
          <a href="#" className="font-medium text-primary hover:underline">
            Forgot password?
          </a>
        </div>
        {error && (
          <p className="text-sm text-destructive" role="alert">
            {error}
          </p>
        )}
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Logging in…
            </>
          ) : (
            "Log in"
          )}
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
    const password = f.get("password")?.toString() || "";
    const confirm = f.get("confirm")?.toString() || "";

    if (password !== confirm) {
      return setError("Passwords don't match.");
    }

    const email = f.get("email")?.toString().trim() || "";
    const payload = {
      username: f.get("username")?.toString().trim() || "",
      email,
      phone_number: f.get("phone_number")?.toString().trim() || "",
      password,
      full_name: f.get("full_name")?.toString().trim() || undefined,
    };

    setLoading(true);
    try {
      await register(payload);
      if (typeof window !== "undefined") {
        sessionStorage.setItem("otp_email", email);
      }
      navigate({ to: "/verify-otp" });
    } catch (err) {
      setError(err.message || "Registration failed. Please check the fields and try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout
      title="Create your account"
      subtitle="Join learners practicing English every day."
      footer={
        <>
          Already have an account?{" "}
          <Link to="/login" className="font-semibold text-primary hover:underline">
            Login
          </Link>
        </>
      }
    >
      <form onSubmit={submit} className="space-y-4">
        <Input
          name="username"
          label="Username"
          icon={AtSign}
          placeholder="cool_username"
          minLength={3}
          maxLength={30}
          pattern="[a-zA-Z0-9_]+"
          title="Letters, numbers and underscores only (min 3 chars)"
          required
        />
        <Input name="email" label="Email" type="email" icon={Mail} placeholder="you@example.com" required />
        <Input
          name="phone_number"
          label="Phone Number"
          icon={Phone}
          placeholder="+919876543210"
          required
          title="E.164 format e.g. +919876543210"
        />
        <Input
          name="password"
          label="Password"
          type="password"
          icon={Lock}
          placeholder="Min 8 chars, uppercase, number, symbol"
          minLength={8}
          required
          autoComplete="new-password"
        />
        <Input
          name="confirm"
          label="Confirm Password"
          type="password"
          icon={Lock}
          placeholder="Min 8 chars, uppercase, number, symbol"
          minLength={8}
          required
          autoComplete="new-password"
        />
        <Input name="full_name" label="Full Name" icon={User} placeholder="Your full name" />
        {error && (
          <p className="text-sm text-destructive" role="alert">
            {error}
          </p>
        )}
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Creating account…
            </>
          ) : (
            "Create Account"
          )}
        </Button>
      </form>
    </AuthLayout>
  );
}

// ─── OTP Verification ────────────────────────────────────────────────────────
export function OtpPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [digits, setDigits] = useState(Array(6).fill(""));
  const [seconds, setSeconds] = useState(60);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const refs = useRef([]);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const stored = sessionStorage.getItem("otp_email") || "";
      setEmail(stored);
    }
  }, []);

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
    if (!email) {
      setError("Please provide the email address you registered with.");
      return;
    }
    setError("");
    setInfo("");
    setLoading(true);
    try {
      const otp = digits.join("");
      await verifyEmail(email, otp);
      if (typeof window !== "undefined") {
        sessionStorage.removeItem("otp_email");
      }
      navigate({ to: "/login" });
    } catch (err) {
      setError(err.message || "Invalid OTP. Please check the code and try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    if (!email) {
      setError("Please enter your registered email address first.");
      return;
    }
    setError("");
    setInfo("");
    setResending(true);
    try {
      await resendOtp(email);
      setInfo(`New OTP sent to ${email}.`);
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
      subtitle={email ? `We sent a 6-digit code to ${email}.` : "Enter your email and the 6-digit code."}
    >
      <Link to="/register" className="mb-5 -mt-2 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-4 w-4" /> Back to Register
      </Link>

      {!sessionStorage?.getItem?.("otp_email") && (
        <div className="mb-4">
          <Input
            label="Email Address"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            required
          />
        </div>
      )}

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
        {info && <p className="mt-3 text-sm text-success" role="status">{info}</p>}
        {error && <p className="mt-3 text-sm text-destructive" role="alert">{error}</p>}
        <Button type="submit" className="mt-6 w-full" disabled={!complete || loading}>
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Verifying…
            </>
          ) : (
            "Verify Email"
          )}
        </Button>
      </form>
      <p className="mt-5 text-center text-sm text-muted-foreground">
        {seconds > 0 ? (
          <>
            Resend code in <span className="font-semibold text-foreground tabular-nums">0:{String(seconds).padStart(2, "0")}</span>
          </>
        ) : (
          <>
            Didn't get it?{" "}
            <button
              type="button"
              onClick={handleResend}
              disabled={resending}
              className="font-semibold text-primary hover:underline disabled:opacity-50"
            >
              {resending ? "Sending…" : "Resend OTP"}
            </button>
          </>
        )}
      </p>
    </AuthLayout>
  );
}
