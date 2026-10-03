import { UserPlus, Sparkles, MessageCircle, Video, Globe2, ShieldCheck, Heart } from "lucide-react";
import Logo from "@/components/tt/Logo";
import Button from "@/components/tt/Button";
import Avatar from "@/components/tt/Avatar";

const steps = [
  { icon: UserPlus, title: "Create your profile", text: "Tell us your native language, English level and what you love talking about." },
  { icon: Sparkles, title: "Get matched", text: "We suggest partners who share your interests and learning goals." },
  { icon: MessageCircle, title: "Start talking", text: "Chat, then hop on a voice or video call when you feel ready." },
];

const features = [
  { icon: Heart, title: "Interest-based matching", text: "Talk about music, tech or travel — conversations flow when you care." },
  { icon: Video, title: "Voice & video calls", text: "Practice real speaking, not just typing, in one tap." },
  { icon: Globe2, title: "Learners worldwide", text: "Meet people from India, Spain, Japan and beyond." },
  { icon: ShieldCheck, title: "Safe & friendly", text: "Block anyone instantly. Respect is our community rule." },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-4 py-5 sm:px-6">
        <Logo />
        <div className="flex gap-2">
          <Button to="/login" variant="ghost" size="sm">Log in</Button>
          <Button to="/register" size="sm">Sign up</Button>
        </div>
      </header>

      <section className="hero-glow">
        <div className="mx-auto grid max-w-6xl items-center gap-12 px-4 py-16 sm:px-6 lg:grid-cols-2 lg:py-24">
          <div>
            <span className="inline-flex items-center gap-2 rounded-full bg-card px-3 py-1 text-xs font-semibold text-primary shadow-soft">
              <span className="h-2 w-2 rounded-full bg-success" /> 2,400 learners online now
            </span>
            <h1 className="mt-5 text-4xl font-extrabold leading-[1.05] sm:text-6xl">
              Practice languages.<br />Meet people.<br /><span className="text-primary">Build confidence.</span>
            </h1>
            <p className="mt-5 max-w-md text-lg text-muted-foreground">
              TalkTribe pairs you with friendly learners around the world so you can practice English through real conversations.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Button to="/register" size="lg">Find Language Partners</Button>
              <Button to="/login" size="lg" variant="outline">Start Learning</Button>
            </div>
          </div>

          <div className="relative mx-auto w-full max-w-md" aria-hidden="true">
            <div className="card-surface rotate-[-2deg] p-5">
              <div className="flex items-center gap-3 border-b pb-4">
                <Avatar name="Priya Nair" online />
                <div>
                  <p className="font-semibold">Priya Nair</p>
                  <p className="text-xs text-muted-foreground">Designer · Advanced English</p>
                </div>
              </div>
              <div className="space-y-3 pt-4 text-sm">
                <p className="w-fit max-w-[80%] rounded-2xl rounded-bl-md bg-muted px-4 py-2.5">Hi! Want to practice talking about travel?</p>
                <p className="ml-auto w-fit max-w-[80%] rounded-2xl rounded-br-md bg-primary px-4 py-2.5 text-primary-foreground">Yes! I just came back from Goa 🌴</p>
                <p className="w-fit max-w-[80%] rounded-2xl rounded-bl-md bg-muted px-4 py-2.5">Tell me everything 😄</p>
              </div>
            </div>
            <div className="card-surface absolute -bottom-8 -left-6 flex items-center gap-3 p-3 pr-5 rotate-[3deg]">
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent text-accent-foreground"><Video className="h-5 w-5" /></span>
              <div>
                <p className="text-sm font-semibold">Call started</p>
                <p className="text-xs text-muted-foreground">with Rahul · 12:04</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
        <h2 className="text-center text-3xl font-bold sm:text-4xl">How TalkTribe works</h2>
        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {steps.map((s, i) => (
            <div key={s.title} className="relative">
              <span className="font-display text-6xl font-extrabold text-primary-soft">0{i + 1}</span>
              <div className="-mt-6 flex h-12 w-12 items-center justify-center rounded-2xl bg-primary text-primary-foreground"><s.icon className="h-5 w-5" /></div>
              <h3 className="mt-4 text-xl font-bold">{s.title}</h3>
              <p className="mt-2 text-muted-foreground">{s.text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="bg-card py-20">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <h2 className="text-3xl font-bold sm:text-4xl">Everything you need to speak up</h2>
          <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {features.map((f) => (
              <div key={f.title} className="card-surface card-hover p-6">
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary-soft text-primary"><f.icon className="h-5 w-5" /></div>
                <h3 className="mt-4 text-lg font-bold">{f.title}</h3>
                <p className="mt-1.5 text-sm text-muted-foreground">{f.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-20 text-center sm:px-6">
        <h2 className="text-3xl font-bold sm:text-4xl">Your tribe is waiting.</h2>
        <p className="mt-3 text-muted-foreground">Free to join. Your first conversation is minutes away.</p>
        <Button to="/register" size="lg" className="mt-7">Create free account</Button>
      </section>

      <footer className="border-t">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-4 py-8 text-sm text-muted-foreground sm:flex-row sm:px-6">
          <Logo />
          <p>© 2026 TalkTribe. Made for curious learners.</p>
        </div>
      </footer>
    </div>
  );
}
