import { useState, useEffect } from "react";
import { useNavigate } from "@tanstack/react-router";
import { Camera, Check } from "lucide-react";
import AuthLayout from "@/layouts/AuthLayout";
import Input, { Textarea, Select } from "@/components/tt/Input";
import Button from "@/components/tt/Button";
import Avatar from "@/components/tt/Avatar";
import InterestChip from "@/components/tt/InterestChip";
import { useUser } from "@/context/UserContext";
import { LANGUAGES, PROFICIENCY_LEVELS, PROFESSIONS } from "@/data/mockData";
import { getInterests, getMyInterests, setMyInterests } from "@/services/api";

const STEPS = ["Basic Information", "Languages", "Interests"];

function Stepper({ step }) {
  return (
    <ol className="mb-8 flex items-center gap-2">
      {STEPS.map((s, i) => (
        <li key={s} className="flex flex-1 items-center gap-2">
          <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold transition ${i < step ? "bg-primary text-primary-foreground" : i === step ? "bg-primary-soft text-primary ring-2 ring-primary" : "bg-muted text-muted-foreground"}`}>
            {i < step ? <Check className="h-4 w-4" /> : i + 1}
          </span>
          <span className={`hidden text-xs font-medium sm:block ${i === step ? "text-foreground" : "text-muted-foreground"}`}>{s}</span>
          {i < STEPS.length - 1 && <span className={`h-0.5 flex-1 rounded ${i < step ? "bg-primary" : "bg-border"}`} />}
        </li>
      ))}
    </ol>
  );
}

export function ProfileSetupPage() {
  const navigate = useNavigate();
  const { user, updateUser } = useUser();
  const [step, setStep] = useState(0);
  const [form, setForm] = useState(user);
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const next = (e) => {
    e.preventDefault();
    updateUser(form);
    if (step === 0) setStep(1);
    else navigate({ to: "/interests" });
  };

  return (
    <AuthLayout wide title="Set up your profile" subtitle="Help partners get to know you. You can change this anytime.">
      <Stepper step={step} />
      <form onSubmit={next} className="space-y-4">
        {step === 0 ? (
          <>
            <div className="flex items-center gap-4">
              <Avatar name={form.name} size="lg" />
              <button type="button" className="inline-flex items-center gap-2 rounded-xl border border-input px-4 py-2 text-sm font-medium hover:border-primary hover:text-primary">
                <Camera className="h-4 w-4" /> Upload photo
              </button>
            </div>
            <Input label="Name" value={form.name} onChange={set("name")} required />
            <Select label="Profession" value={form.profession} onChange={set("profession")} options={PROFESSIONS} />
            <Textarea label="Bio" value={form.bio} onChange={set("bio")} placeholder="A few words about you and your goals" maxLength={200} hint={`${form.bio.length}/200`} />
          </>
        ) : (
          <>
            <Select label="Native language" value={form.nativeLanguage} onChange={set("nativeLanguage")} options={LANGUAGES} />
            <Select label="English proficiency" value={form.englishLevel} onChange={set("englishLevel")} options={PROFICIENCY_LEVELS} />
            <Select label="Learning / practice language" value={form.learningLanguage} onChange={set("learningLanguage")} options={LANGUAGES} />
          </>
        )}
        <div className="flex justify-between pt-2">
          {step > 0 ? <Button type="button" variant="ghost" onClick={() => setStep(0)}>Back</Button> : <span />}
          <Button type="submit">Continue</Button>
        </div>
      </form>
    </AuthLayout>
  );
}

const MAX = 10;

export function InterestsPage() {
  const navigate = useNavigate();
  const { user, updateUser } = useUser();
  const { data: interestsList, loading: interestsLoading } = useAsync(getInterests);
  const { data: userInterests, loading: userInterestsLoading } = useAsync(getMyInterests);
  const [selected, setSelected] = useState([]);

  // Initialize selected when userInterests loads
  useEffect(() => {
    if (userInterests) {
      setSelected(userInterests);
    }
  }, [userInterests]);

  const toggle = (i) =>
    setSelected((s) => (s.includes(i) ? s.filter((x) => x !== i) : s.length >= MAX ? s : [...s, i]));
  const done = async () => {
    await setMyInterests({ interest_ids: selected.map((i) => i), custom_interests: [] });
    updateUser({ interests: selected });
    navigate({ to: "/dashboard" });
  };

  return (
    <AuthLayout wide title="What do you love talking about?" subtitle="Pick up to 10 interests. We'll match you with people who share them.">
      <Stepper step={2} />
      <div className="flex flex-wrap gap-2.5">
        {interestsLoading ? <p>Loading interests…</p> : (interestsList || []).map((i) => (
          <InterestChip key={i} label={i} selected={selected.includes(i)} onClick={() => toggle(i)} />
        ))}
      </div>
      <div className="mt-6 flex items-center gap-3">
        <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
          <div className="h-full rounded-full bg-primary transition-all" style={{ width: `${(selected.length / MAX) * 100}%` }} />
        </div>
        <p className="text-sm font-medium tabular-nums" aria-live="polite">{selected.length} / {MAX} interests selected</p>
      </div>
      {selected.length >= MAX && <p className="mt-2 text-xs text-muted-foreground">You've reached the maximum. Deselect one to choose another.</p>}
      <div className="mt-8 flex justify-between">
        <Button variant="ghost" onClick={() => navigate({ to: "/dashboard" })}>Skip</Button>
        <Button onClick={done} disabled={selected.length === 0}>Continue</Button>
      </div>
    </AuthLayout>
  );
}
