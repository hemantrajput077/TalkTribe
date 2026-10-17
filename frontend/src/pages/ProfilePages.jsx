import { useState, useEffect } from "react";
import { useNavigate } from "@tanstack/react-router";
import { LogOut, Pencil, Sparkles, Loader2 } from "lucide-react";
import AppLayout from "@/layouts/AppLayout";
import ProfileCard, { InfoTile } from "@/components/tt/ProfileCard";
import Button from "@/components/tt/Button";
import InterestChip from "@/components/tt/InterestChip";
import Input, { Textarea, Select } from "@/components/tt/Input";
import { useUser } from "@/context/UserContext";
import { LANGUAGES, PROFICIENCY_LEVELS, PROFESSIONS } from "@/data/mockData";

export function ProfilePage() {
  const { user, loading, logout } = useUser();
  const navigate = useNavigate();

  useEffect(() => {
    if (!loading && !user) {
      navigate({ to: "/login" });
    }
  }, [loading, user, navigate]);

  if (loading || !user) {
    return (
      <AppLayout>
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </AppLayout>
    );
  }

  const interests = Array.isArray(user.interests) ? user.interests : [];

  return (
    <AppLayout>
      <ProfileCard person={user}>
        <Button to="/profile/edit"><Pencil className="h-4 w-4" /> Edit Profile</Button>
        <Button
          variant="danger-outline"
          onClick={async () => {
            await logout();
            navigate({ to: "/login" });
          }}
        >
          <LogOut className="h-4 w-4" /> Logout
        </Button>
      </ProfileCard>

      <div className="mt-5 grid gap-5 lg:grid-cols-3">
        <section className="card-surface p-6">
          <h2 className="text-lg font-bold">Languages</h2>
          <div className="mt-4 space-y-3">
            <InfoTile label="Native language" value={user.nativeLanguage || "English"} />
            <InfoTile label="English proficiency" value={user.englishLevel || "Intermediate"} />
            <InfoTile label="Practicing" value={user.learningLanguage || "Spanish"} />
          </div>
        </section>

        <section className="card-surface p-6 lg:col-span-2">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold">Interests</h2>
            <Button to="/interests" variant="secondary" size="sm">
              <Sparkles className="h-4 w-4" /> Edit Interests
            </Button>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            {interests.length > 0 ? (
              interests.map((i) => (
                <InterestChip key={typeof i === "object" ? i.id || i.name : i} label={typeof i === "object" ? i.name : i} />
              ))
            ) : (
              <p className="text-sm text-muted-foreground">No interests selected yet. Click Edit Interests to add some!</p>
            )}
          </div>
        </section>
      </div>
    </AppLayout>
  );
}

export function EditProfilePage() {
  const { user, updateUser, loading } = useUser();
  const navigate = useNavigate();
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    name: "",
    bio: "",
    profession: "Student",
    nativeLanguage: "English",
    englishLevel: "Intermediate (B1-B2)",
    learningLanguage: "Spanish",
  });

  useEffect(() => {
    if (user) {
      setForm({
        name: user.full_name || user.name || user.username || "",
        bio: user.bio || "",
        profession: user.profession || "Student",
        nativeLanguage: user.nativeLanguage || "English",
        englishLevel: user.englishLevel || "Intermediate (B1-B2)",
        learningLanguage: user.learningLanguage || "Spanish",
      });
    }
  }, [user]);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const save = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await updateUser(form);
      navigate({ to: "/profile" });
    } catch (err) {
      console.error("Save failed:", err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <AppLayout>
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <div className="mx-auto max-w-2xl">
        <h1 className="text-3xl font-bold">Edit profile</h1>
        <p className="mt-1 text-muted-foreground">Keep your profile fresh so partners can find you.</p>

        <form onSubmit={save} className="card-surface mt-6 space-y-5 p-6">
          <Input label="Name" value={form.name} onChange={set("name")} required />
          <Textarea
            label="Bio"
            value={form.bio}
            onChange={set("bio")}
            maxLength={200}
            hint={`${form.bio?.length || 0}/200`}
            placeholder="Tell partners about your goals and what you enjoy discussing..."
          />
          <Select label="Profession" value={form.profession} onChange={set("profession")} options={PROFESSIONS} />

          <div className="grid gap-5 sm:grid-cols-2">
            <Select label="Native language" value={form.nativeLanguage} onChange={set("nativeLanguage")} options={LANGUAGES} />
            <Select label="English proficiency" value={form.englishLevel} onChange={set("englishLevel")} options={PROFICIENCY_LEVELS} />
          </div>

          <Select label="Learning language" value={form.learningLanguage} onChange={set("learningLanguage")} options={LANGUAGES} />

          <div className="flex justify-end gap-3 border-t pt-5">
            <Button type="button" variant="ghost" onClick={() => navigate({ to: "/profile" })}>
              Cancel
            </Button>
            <Button type="submit" disabled={saving}>
              {saving ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Saving…</> : "Save Changes"}
            </Button>
          </div>
        </form>
      </div>
    </AppLayout>
  );
}
