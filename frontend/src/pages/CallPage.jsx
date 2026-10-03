import { useEffect, useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { Mic, MicOff, PhoneOff, Video, VideoOff } from "lucide-react";
import Avatar from "@/components/tt/Avatar";
import { useAsync } from "@/hooks/useAsync";
import { getPartnerById } from "@/services/api";
import { useUser } from "@/context/UserContext";

// Visual-only call screen. Video streams will be attached here later.
export default function CallPage({ id }) {
  const navigate = useNavigate();
  const { user } = useUser();
  const { data: partner } = useAsync(() => getPartnerById(id), [id]);
  const [status, setStatus] = useState("Connecting…");
  const [mic, setMic] = useState(true);
  const [cam, setCam] = useState(true);
  const [secs, setSecs] = useState(0);

  useEffect(() => {
    const t = setTimeout(() => setStatus("Connected"), 1800);
    return () => clearTimeout(t);
  }, []);
  useEffect(() => {
    if (status !== "Connected") return;
    const t = setInterval(() => setSecs((s) => s + 1), 1000);
    return () => clearInterval(t);
  }, [status]);

  const name = partner?.name || "Partner";
  const time = `${String(Math.floor(secs / 60)).padStart(2, "0")}:${String(secs % 60).padStart(2, "0")}`;
  const ctrl = "flex h-14 w-14 items-center justify-center rounded-full transition hover:scale-105";

  return (
    <div className="relative flex h-dvh flex-col overflow-hidden bg-call text-call-foreground">
      <div className="absolute inset-0 flex flex-col items-center justify-center gap-4">
        <div className={status === "Connected" ? "" : "animate-pulse"}>
          <Avatar name={name} size="xl" />
        </div>
        <p className="font-display text-2xl font-bold">{name}</p>
      </div>

      <header className="relative z-10 flex items-center justify-between p-5">
        <span className="inline-flex items-center gap-2 rounded-full bg-call-foreground/10 px-3 py-1.5 text-sm backdrop-blur">
          <span className={`h-2 w-2 rounded-full ${status === "Connected" ? "bg-success" : "bg-warm animate-pulse"}`} />
          {status}{status === "Connected" && ` · ${time}`}
        </span>
      </header>

      <div className="absolute bottom-32 right-5 z-10 flex h-44 w-32 items-center justify-center overflow-hidden rounded-2xl border border-call-foreground/15 bg-call-foreground/10 backdrop-blur sm:h-56 sm:w-40">
        {cam ? <Avatar name={user.name} size="lg" /> : <VideoOff className="h-6 w-6 opacity-60" />}
        <span className="absolute bottom-2 left-2 text-[11px] opacity-80">You</span>
      </div>

      <div className="relative z-10 mt-auto flex items-center justify-center gap-4 p-8">
        <button onClick={() => setMic((m) => !m)} aria-label={mic ? "Mute microphone" : "Unmute microphone"} aria-pressed={!mic} className={`${ctrl} ${mic ? "bg-call-foreground/15" : "bg-call-foreground text-call"}`}>
          {mic ? <Mic className="h-6 w-6" /> : <MicOff className="h-6 w-6" />}
        </button>
        <button onClick={() => setCam((c) => !c)} aria-label={cam ? "Turn camera off" : "Turn camera on"} aria-pressed={!cam} className={`${ctrl} ${cam ? "bg-call-foreground/15" : "bg-call-foreground text-call"}`}>
          {cam ? <Video className="h-6 w-6" /> : <VideoOff className="h-6 w-6" />}
        </button>
        <button onClick={() => navigate({ to: "/conversations" })} aria-label="End call" className={`${ctrl} h-16 w-16 bg-destructive text-destructive-foreground`}>
          <PhoneOff className="h-7 w-7" />
        </button>
      </div>
    </div>
  );
}
