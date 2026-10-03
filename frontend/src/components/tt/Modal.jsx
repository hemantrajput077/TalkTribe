import { useEffect } from "react";

export default function Modal({ open, onClose, title, children, footer }) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" role="dialog" aria-modal="true">
      <div className="absolute inset-0 bg-foreground/40 backdrop-blur-sm animate-in fade-in" onClick={onClose} />
      <div className="card-surface relative w-full max-w-sm p-6 animate-in zoom-in-95 fade-in">
        <h3 className="text-xl font-bold">{title}</h3>
        <div className="mt-2 text-sm text-muted-foreground">{children}</div>
        {footer && <div className="mt-6 flex justify-end gap-3">{footer}</div>}
      </div>
    </div>
  );
}
