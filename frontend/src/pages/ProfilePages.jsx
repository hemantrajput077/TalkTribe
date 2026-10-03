import { useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { LogOut, Pencil, Sparkles } from "lucide-react";
import AppLayout from "@/layouts/AppLayout";
import ProfileCard, { InfoTile } from "@/components/tt/ProfileCard";
import Button from "@/components/tt/Button";
import InterestChip from "@/components/tt/InterestChip";
import Input, { Textarea, Select } from "@/components/tt/Input";
import { useUser } from "@/context/UserContext";
import { LANGUAGES, PROFICIENCY_LEVELS, PROFESSIONS } from "@/data/mockData";

export function ProfilePage() {
  const { user, logout } = useUser();
  const navigate = useNavigate();
  return (
    <AppLayout>
      <ProfileCard person={user}>
        <Button to="/profile/edit"><Pencil className="h-4 w-4" /> Edit Profile</Button>
        <Button variant="danger-outline" onClick={() => { logout(); navigate({ to: "/login" }); }}>
          <LogOut className="h-4 w-4" /> Logout
        </Button>
      </ProfileCard>
      <div className="mt-5 grid gap-5 lg:grid-cols-3">
        <section className="card-surface p-6">
          <h2 className="text-lg font-bold">Languages</h2>
          <div className="mt-4 space-y-3">
            <InfoTile label="Native language" value={user.nativeLanguage} />
            <InfoTile label="English proficiency" value={user.englishLevel} />
            <InfoTile label="Practicing" value={user.learningLanguage} />
          </div>
        </section>
        <section className="card-surface p-6 lg:col-span-2">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold">Interests</h2>
            <Button to="/interests" variant="secondary" size="sm"><Sparkles className="h-4 w-4" /> Edit Interests</Button>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            {user.interests.map((i) => <InterestChip key={i} label={i} />)}
          </div>
        </section>
      </div>
    </AppLayout>
  );
}

export function EditProfilePage() {
  const { user, updateUser } = useUser();
  const navigate = useNavigate();
  const [form, setForm] = useState(user);
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));
  const save = (e) => {
    e.preventDefault();
    updateUser(form);
    navigate({ to: "/profile" });
  };
  return (
    <AppLayout>
      <div className="mx-auto max-w-2xl">
        <h1 className="text-3xl font-bold">Edit profile</h1>
        <p className="mt-1 text-muted-foreground">Keep your profile fresh so partners can find you.</p>
        <form onSubmit={save} className="card-surface mt-6 space-y-5 p-6">
          <Input label="Name" value={form.name} onChange={set("name")} required />
          <Textarea label="Bio" value={form.bio} onChange={set("bio")} maxLength={200} hint={`${form.bio.length}/200`} />
          <Select label="Profession" value={form.profession} onChange={set("profession")} options={PROFESSIONS} />
          <div className="grid gap-5 sm:grid-cols-2">
            <Select label="Native language" value={form.nativeLanguage} onChange={set("nativeLanguage")} options={LANGUAGES} />
            <Select label="English proficiency" value={form.englishLevel} onChange={set("englishLevel")} options={PROFICIENCY_LEVELS} />
          </div>
          <Select label="Learning language" value={form.learningLanguage} onChange={set("learningLanguage")} options={LANGUAGES} />
          <div className="flex justify-end gap-3 border-t pt-5">
            <Button type="button" variant="ghost" onClick={() => navigate({ to: "/profile" })}>Cancel</Button>
            <Button type="submit">Save Changes</Button>
          </div>
        </form>
      </div>
    </AppLayout>
  );
}
