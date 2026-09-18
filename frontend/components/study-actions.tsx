"use client";

import { useState } from "react";
import { BookMarked, FileDown, FileText, Loader2, Sparkles } from "lucide-react";
import { MarkdownContent } from "@/components/markdown-content";
import { generateStudyAction } from "@/lib/api";
import { downloadAsDocx, downloadAsPdf } from "@/lib/markdown-export";
import type { StudyActionResponse } from "@/lib/types";

type StudyActionsProps = {
  projectId: string | null;
  selectedTopicIds: string[];
  onResult?: (result: StudyActionResponse) => void;
};

export function StudyActions({ projectId, selectedTopicIds, onResult }: StudyActionsProps) {
  const [result, setResult] = useState<StudyActionResponse | null>(null);
  const [loadingAction, setLoadingAction] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function runAction(endpoint: "summary" | "simple-explanation") {
    if (!projectId) return;

    setLoadingAction(endpoint);
    setError(null);

    try {
      const response = await generateStudyAction(endpoint, projectId, selectedTopicIds);
      setResult(response);
      onResult?.(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo generar el contenido.");
    } finally {
      setLoadingAction(null);
    }
  }

  const disabled = !projectId || selectedTopicIds.length === 0 || Boolean(loadingAction);

  return (
    <section className="panel rounded-lg p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-white">Estudio</h2>
          <p className="mt-1 text-sm text-slate-400">
            {selectedTopicIds.length
              ? `${selectedTopicIds.length} tema(s) seleccionado(s)`
              : "Selecciona temas para activar acciones"}
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => runAction("summary")}
            disabled={disabled}
            className="inline-flex h-10 items-center gap-2 rounded-md border border-slate-700 bg-slate-900 px-3 text-sm font-medium text-slate-100 transition hover:border-sky-300/50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loadingAction === "summary" ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <BookMarked size={16} />
            )}
            Resumen
          </button>
          <button
            type="button"
            onClick={() => runAction("simple-explanation")}
            disabled={disabled}
            className="inline-flex h-10 items-center gap-2 rounded-md bg-violet-300 px-3 text-sm font-semibold text-slate-950 transition hover:bg-violet-200 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loadingAction === "simple-explanation" ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <Sparkles size={16} />
            )}
            Explicacion simple
          </button>
        </div>
      </div>

      {error ? (
        <div className="mt-4 rounded-md border border-red-400/30 bg-red-950/35 px-3 py-2 text-sm text-red-100">
          {error}
        </div>
      ) : null}

      {result ? (
        <article className="mt-4 rounded-lg border border-slate-800 bg-slate-950/45 p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 className="text-sm font-semibold uppercase tracking-[0.14em] text-sky-200">
              {result.title}
            </h3>
            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={() => downloadAsPdf(result.title, result.content)}
                className="inline-flex h-7 items-center gap-1.5 rounded-md border border-slate-700 px-2 text-xs text-slate-300 transition hover:border-sky-300/50 hover:text-sky-100"
              >
                <FileText size={12} />
                PDF
              </button>
              <button
                type="button"
                onClick={() => downloadAsDocx(result.title, result.content)}
                className="inline-flex h-7 items-center gap-1.5 rounded-md border border-slate-700 px-2 text-xs text-slate-300 transition hover:border-sky-300/50 hover:text-sky-100"
              >
                <FileDown size={12} />
                DOCX
              </button>
            </div>
          </div>
          <MarkdownContent content={result.content} className="mt-3 text-sm leading-7 text-slate-200" />
        </article>
      ) : null}
    </section>
  );
}

