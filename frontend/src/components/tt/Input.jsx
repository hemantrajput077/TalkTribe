import { useId, useState } from "react";
import { Eye, EyeOff } from "lucide-react";

const field =
  "w-full rounded-xl border border-input bg-card px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground transition focus:border-primary focus:outline-none focus:ring-4 focus:ring-primary/15";

function Wrap({ id, label, hint, children }) {
  return (
    <div className="space-y-1.5">
      {label && (
        <label htmlFor={id} className="block text-sm font-medium text-foreground">
          {label}
        </label>
      )}
      {children}
      {hint && <p className="text-xs text-muted-foreground">{hint}</p>}
    </div>
  );
}

export default function Input({ label, hint, type = "text", icon: Icon, className = "", ...props }) {
  const id = useId();
  const [show, setShow] = useState(false);
  const isPw = type === "password";
  return (
    <Wrap id={id} label={label} hint={hint}>
      <div className="relative">
        {Icon && <Icon className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />}
        <input
          id={id}
          type={isPw && show ? "text" : type}
          className={`${field} ${Icon ? "pl-10" : ""} ${isPw ? "pr-11" : ""} ${className}`}
          {...props}
        />
        {isPw && (
          <button
            type="button"
            onClick={() => setShow((s) => !s)}
            aria-label={show ? "Hide password" : "Show password"}
            className="absolute right-3 top-1/2 -translate-y-1/2 rounded-md p-1 text-muted-foreground hover:text-foreground"
          >
            {show ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        )}
      </div>
    </Wrap>
  );
}

export function Textarea({ label, hint, ...props }) {
  const id = useId();
  return (
    <Wrap id={id} label={label} hint={hint}>
      <textarea id={id} rows={4} className={`${field} resize-none`} {...props} />
    </Wrap>
  );
}

export function Select({ label, hint, options, ...props }) {
  const id = useId();
  return (
    <Wrap id={id} label={label} hint={hint}>
      <select id={id} className={`${field} appearance-none`} {...props}>
        {options.map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
    </Wrap>
  );
}
