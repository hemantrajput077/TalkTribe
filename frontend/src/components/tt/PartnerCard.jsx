import { useState } from "react";
import { Check, UserPlus } from "lucide-react";
import Avatar from "./Avatar";
import Button from "./Button";
import InterestChip from "./InterestChip";

export default function PartnerCard({ partner, myInterests = [] }) {
  const [connected, setConnected] = useState(false);
  const shared = partner.interests.filter((i) => myInterests.includes(i));
  return (
    <article className="card-surface card-hover flex flex-col p-5">
      <div className="flex items-start gap-3">
        <Avatar name={partner.name} online={partner.online} />
        <div className="min-w-0">
          <h3 className="truncate text-base font-bold">{partner.name}</h3>
          <p className="text-sm text-muted-foreground">{partner.profession}</p>
        </div>
      </div>
      <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
        <div className="rounded-lg bg-muted px-3 py-2">
          <p className="text-muted-foreground">English</p>
          <p className="font-semibold">{partner.englishLevel}</p>
        </div>
        <div className="rounded-lg bg-muted px-3 py-2">
          <p className="text-muted-foreground">Native</p>
          <p className="font-semibold">{partner.nativeLanguage}</p>
        </div>
      </div>
      <p className="mt-3 line-clamp-2 text-sm text-muted-foreground">{partner.bio}</p>
      {shared.length > 0 && (
        <div className="mt-3">
          <p className="mb-1.5 text-xs font-medium text-muted-foreground">Shared interests</p>
          <div className="flex flex-wrap gap-1.5">
            {shared.map((i) => <InterestChip key={i} label={i} shared size="sm" />)}
          </div>
        </div>
      )}
      <div className="mt-auto flex gap-2 pt-5">
        <Button to="/partners/$id" params={{ id: partner.id }} variant="outline" size="sm" className="flex-1">
          View Profile
        </Button>
        <Button size="sm" variant={connected ? "secondary" : "primary"} className="flex-1" onClick={() => setConnected((c) => !c)}>
          {connected ? <><Check className="h-4 w-4" /> Requested</> : <><UserPlus className="h-4 w-4" /> Connect</>}
        </Button>
      </div>
    </article>
  );
}
