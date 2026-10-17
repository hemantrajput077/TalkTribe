import { useState } from "react";
import { Check, UserPlus } from "lucide-react";
import Avatar from "./Avatar";
import Button from "./Button";
import InterestChip from "./InterestChip";

export default function PartnerCard({ partner, myInterests = [] }) {
  const [connected, setConnected] = useState(false);

  const partnerInterests = Array.isArray(partner?.interests)
    ? partner.interests
    : Array.isArray(partner?.shared_interests)
    ? partner.shared_interests
    : [];

  const safeMyInterests = Array.isArray(myInterests)
    ? myInterests.map((i) => (typeof i === "object" ? i.name : i))
    : [];

  const shared = partnerInterests.filter((i) => {
    const label = typeof i === "object" ? i.name : i;
    return safeMyInterests.includes(label);
  });

  const partnerName = partner?.name || partner?.display_name || "Partner";

  return (
    <article className="card-surface card-hover flex flex-col p-5">
      <div className="flex items-start gap-3">
        <Avatar name={partnerName} online={partner?.online ?? true} />
        <div className="min-w-0">
          <h3 className="truncate text-base font-bold">{partnerName}</h3>
          <p className="text-sm text-muted-foreground">{partner?.profession || "Language Learner"}</p>
        </div>
      </div>
      <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
        <div className="rounded-lg bg-muted px-3 py-2">
          <p className="text-muted-foreground">English</p>
          <p className="font-semibold">{partner?.englishLevel || partner?.proficiency_level || "Intermediate"}</p>
        </div>
        <div className="rounded-lg bg-muted px-3 py-2">
          <p className="text-muted-foreground">Native</p>
          <p className="font-semibold">{partner?.nativeLanguage || "English"}</p>
        </div>
      </div>
      <p className="mt-3 line-clamp-2 text-sm text-muted-foreground">
        {partner?.bio || "Practicing English on TalkTribe."}
      </p>
      {shared.length > 0 && (
        <div className="mt-3">
          <p className="mb-1.5 text-xs font-medium text-muted-foreground">Shared interests</p>
          <div className="flex flex-wrap gap-1.5">
            {shared.map((i) => {
              const label = typeof i === "object" ? i.name : i;
              return <InterestChip key={label} label={label} shared size="sm" />;
            })}
          </div>
        </div>
      )}
      <div className="mt-auto flex gap-2 pt-5">
        <Button to="/partners/$id" params={{ id: String(partner?.id ?? "1") }} variant="outline" size="sm" className="flex-1">
          View Profile
        </Button>
        <Button
          size="sm"
          variant={connected ? "secondary" : "primary"}
          className="flex-1"
          onClick={() => setConnected((c) => !c)}
        >
          {connected ? (
            <>
              <Check className="h-4 w-4" /> Requested
            </>
          ) : (
            <>
              <UserPlus className="h-4 w-4" /> Connect
            </>
          )}
        </Button>
      </div>
    </article>
  );
}
