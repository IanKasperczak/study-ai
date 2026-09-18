"use client";

import { Check, Trash2, X } from "lucide-react";
import { useEffect, useState } from "react";

type ConfirmDeleteButtonProps = {
  onConfirm: () => void;
  label: string;
  size?: number;
};

// A native window.confirm() looks out of place in this dark UI and can't be
// driven reliably by browser automation either -- this two-tap pattern
// (tap to arm, tap again within a few seconds to confirm) replaces it.
export function ConfirmDeleteButton({ onConfirm, label, size = 14 }: ConfirmDeleteButtonProps) {
  const [confirming, setConfirming] = useState(false);

  useEffect(() => {
    if (!confirming) return;
    const timeout = window.setTimeout(() => setConfirming(false), 3000);
    return () => window.clearTimeout(timeout);
  }, [confirming]);

  if (confirming) {
    return (
      <div className="flex shrink-0 items-center gap-1">
        <button
          type="button"
          onClick={(event) => {
            event.stopPropagation();
            setConfirming(false);
            onConfirm();
          }}
          className="grid h-6 w-6 shrink-0 place-items-center rounded bg-red-400/20 text-red-300 transition hover:bg-red-400/30"
          aria-label={`Confirmar: ${label}`}
        >
          <Check size={size - 1} />
        </button>
        <button
          type="button"
          onClick={(event) => {
            event.stopPropagation();
            setConfirming(false);
          }}
          className="grid h-6 w-6 shrink-0 place-items-center rounded text-slate-500 transition hover:text-slate-300"
          aria-label="Cancelar"
        >
          <X size={size - 1} />
        </button>
      </div>
    );
  }

  return (
    <button
      type="button"
      onClick={(event) => {
        event.stopPropagation();
        setConfirming(true);
      }}
      className="grid h-6 w-6 shrink-0 place-items-center rounded text-slate-500 transition hover:text-red-300"
      aria-label={label}
    >
      <Trash2 size={size} />
    </button>
  );
}
