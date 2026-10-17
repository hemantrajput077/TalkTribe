import { useState } from "react";
import { ArrowLeft, Ban, Check, MessageCircle, UserPlus, UserX } from "lucide-react";
import { Link, useNavigate } from "@tanstack/react-router";
import AppLayout from "@/layouts/AppLayout";
import ProfileCard, { InfoTile } from "@/components/tt/ProfileCard";
import Button from "@/components/tt/Button";
import Modal from "@/components/tt/Modal";
import InterestChip from "@/components/tt/InterestChip";
import { LoadingState, EmptyState } from "@/components/tt/States";
import { useUser } from "@/context/UserContext";
import { useAsync } from "@/hooks/useAsync";
import { getPartnerById } from "@/services/api";

export default function PartnerProfilePage({ id }) {
  const navigate = useNavigate();
  const { user } = useUser();
  const { data: partner, loading } = useAsync(() => getPartnerById(id), [id]);
  const [connected, setConnected] = useState(false);
  const [blockOpen, setBlockOpen] = useState(false);
  const [blocked, setBlocked] = useState(false);

  if (loading) return <AppLayout><LoadingState label="Loading profile…" /></AppLayout>;
  if (!partner)
    return (
      <AppLayout>
        <EmptyState icon={UserX} title="Profile not found" description="This learner may have left TalkTribe." action={<Button to="/partners">Back to partners</Button>} />
      </AppLayout>
    );

  const safePartnerInterests = Array.isArray(partner.interests)
    ? partner.interests
    : Array.isArray(partner.shared_interests)
    ? partner.shared_interests
    : [];

  const safeUserInterests = Array.isArray(user?.interests)
    ? user.interests.map((i) => (typeof i === "object" ? i.name : i))
    : [];

  const shared = safePartnerInterests.filter((i) => {
    const label = typeof i === "object" ? i.name : i;
    return safeUserInterests.includes(label);
  });

  const partnerName = partner.name || partner.display_name || "Partner";
  const first = partnerName.split(" ")[0];

  return (
    <AppLayout>
      <Link to="/partners" className="mb-4 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-4 w-4" /> Back to partners
      </Link>

      {blocked && (
        <div className="mb-4 rounded-xl bg-destructive/10 px-4 py-3 text-sm text-destructive" role="status">
          You blocked {first}. You won't see each other anymore.
        </div>
      )}

      <ProfileCard
        person={partner}
        badge={partner.online && <span className="rounded-full bg-success/15 px-2 py-0.5 text-xs font-semibold text-success">Online</span>}
      >
        <Button onClick={() => navigate({ to: "/conversations" })} disabled={blocked}>
          <MessageCircle className="h-4 w-4" /> Start Conversation
        </Button>
        <Button variant={connected ? "secondary" : "outline"} onClick={() => setConnected((c) => !c)} disabled={blocked}>
          {connected ? <><Check className="h-4 w-4" /> Requested</> : <><UserPlus className="h-4 w-4" /> Connect</>}
        </Button>
        <Button variant="danger-outline" onClick={() => setBlockOpen(true)} disabled={blocked} aria-label="Block">
          <Ban className="h-4 w-4" /> Block
        </Button>
      </ProfileCard>

      <div className="mt-5 grid gap-5 lg:grid-cols-3">
        <section className="card-surface p-6">
          <h2 className="text-lg font-bold">Languages</h2>
          <div className="mt-4 space-y-3">
            <InfoTile label="Native language" value={partner.nativeLanguage || "English"} />
            <InfoTile label="English proficiency" value={partner.englishLevel || partner.proficiency_level || "Intermediate"} />
            <InfoTile label="Learning language" value={partner.learningLanguage || "Spanish"} />
          </div>
        </section>
        <section className="card-surface p-6 lg:col-span-2">
          <h2 className="text-lg font-bold">Shared interests</h2>
          <p className="text-sm text-muted-foreground">Great conversation starters with {first}.</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {shared.length ? (
              shared.map((i) => {
                const label = typeof i === "object" ? i.name : i;
                return <InterestChip key={label} label={label} shared />;
              })
            ) : (
              <p className="text-sm text-muted-foreground">No shared interests yet.</p>
            )}
          </div>
          <h2 className="mt-7 text-lg font-bold">All interests</h2>
          <div className="mt-3 flex flex-wrap gap-2">
            {safePartnerInterests.map((i) => {
              const label = typeof i === "object" ? i.name : i;
              return <InterestChip key={label} label={label} />;
            })}
          </div>
        </section>
      </div>

      <Modal
        open={blockOpen}
        onClose={() => setBlockOpen(false)}
        title={`Block ${first}?`}
        footer={
          <>
            <Button variant="ghost" onClick={() => setBlockOpen(false)}>Cancel</Button>
            <Button variant="danger" onClick={() => { setBlocked(true); setBlockOpen(false); }}>Block</Button>
          </>
        }
      >
        You won't be able to interact with this user.
      </Modal>
    </AppLayout>
  );
}
