"use client";

import { HelpCircle, Loader2, RotateCcw } from "lucide-react";
import type { QuizAttempt, QuizSession, Topic } from "@/lib/types";

type QuizPanelProps = {
  projectId: string | null;
  selectedTopicIds: string[];
  session: QuizSession | null;
  isGenerating: boolean;
  error: string | null;
  onStart: (topicIds: string[]) => void;
  onResume: () => void;
};

export function QuizPanel({
  projectId,
  selectedTopicIds,
  session,
  isGenerating,
  error,
  onStart,
  onResume
}: QuizPanelProps) {
  const inProgress = Boolean(session && !session.graded);
  const canStart = Boolean(projectId) && selectedTopicIds.length > 0 && !isGenerating;

  return (
    <div className="space-y-2">
      <button
        type="button"
        onClick={() => (inProgress ? onResume() : onStart(selectedTopicIds))}
        disabled={inProgress ? false : !canStart}
        className={`relative w-full rounded-lg border p-3 text-left transition disabled:cursor-not-allowed disabled:opacity-50 ${
          inProgress
            ? "border-sky-300/50 bg-sky-300/5 hover:border-sky-300/70"
            : "border-emerald-300/40 bg-emerald-300/5 hover:border-emerald-300/60"
        }`}
      >
        <span
          className={`absolute right-2 top-2 rounded-full border px-2 py-0.5 text-[10px] uppercase tracking-wide ${
            inProgress
              ? "border-sky-300/50 bg-slate-900 text-sky-200"
              : "border-emerald-300/50 bg-slate-900 text-emerald-200"
          }`}
        >
          {inProgress ? "En progreso" : "Disponible"}
        </span>
        <div className="flex items-start gap-3 pr-20">
          <div
            className={`mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-md border ${
              inProgress ? "border-sky-300/50 text-sky-300" : "border-emerald-300/50 text-emerald-300"
            }`}
          >
            {isGenerating ? <Loader2 size={15} className="animate-spin" /> : <HelpCircle size={15} />}
          </div>
          <div className="min-w-0">
            <h3 className="text-sm font-medium text-white">
              {inProgress ? "Continuar quiz" : "Quiz"}
            </h3>
            <p className="mt-1 text-xs leading-5 text-slate-400">
              {inProgress
                ? "Tenes un quiz sin terminar."
                : selectedTopicIds.length
                  ? `10 preguntas sobre ${selectedTopicIds.length} tema(s) seleccionado(s).`
                  : "Selecciona temas en la barra de la izquierda para generar uno."}
            </p>
          </div>
        </div>
      </button>

      {error ? (
        <div className="rounded-md border border-red-400/30 bg-red-950/35 px-3 py-2 text-xs text-red-100">
          {error}
        </div>
      ) : null}
    </div>
  );
}

type QuizHistoryProps = {
  projectId: string | null;
  topics: Topic[];
  attempts: QuizAttempt[];
  isGenerating: boolean;
  onRetake: (topicIds: string[]) => void;
};

export function QuizHistory({ projectId, topics, attempts, isGenerating, onRetake }: QuizHistoryProps) {
  if (!attempts.length) return null;

  function topicLabel(topicIdList: string): string {
    const ids = topicIdList.split(",").filter(Boolean);
    const titles = ids.map((id) => topics.find((topic) => topic.id === id)?.title ?? id);
    return titles.join(" + ") || "Tema eliminado";
  }

  return (
    <div className="space-y-1.5">
      {attempts.slice(0, 8).map((attempt) => (
        <div
          key={attempt.id}
          className="flex items-center justify-between gap-2 rounded-md border border-slate-800 bg-slate-950/30 px-2.5 py-1.5 text-xs"
        >
          <span className="min-w-0 truncate text-slate-300">{topicLabel(attempt.subtema_id)}</span>
          <div className="flex shrink-0 items-center gap-2">
            <span className="font-medium text-slate-200">
              {attempt.score}/{attempt.total_questions}
            </span>
            <button
              type="button"
              onClick={() => onRetake(attempt.subtema_id.split(",").filter(Boolean))}
              disabled={!projectId || isGenerating}
              className="grid h-6 w-6 shrink-0 place-items-center rounded text-slate-500 transition hover:text-sky-300 disabled:cursor-not-allowed disabled:opacity-40"
              aria-label="Repetir este quiz"
            >
              <RotateCcw size={13} />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
