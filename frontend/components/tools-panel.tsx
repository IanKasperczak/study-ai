"use client";

import {
  BookMarked,
  ChevronLeft,
  ChevronsLeft,
  ChevronsRight,
  HelpCircle,
  Layers,
  Mic,
  Wand2
} from "lucide-react";
import { QuizPanel } from "@/components/quiz-panel";
import type { StudyActionResponse, Topic } from "@/lib/types";

type ToolsPanelProps = {
  collapsed: boolean;
  onToggleCollapsed: () => void;
  projectId: string | null;
  topics: Topic[];
  latestStudyResult: StudyActionResponse | null;
};

const PLACEHOLDER_TOOLS = [
  {
    icon: Mic,
    label: "Voz y audio",
    description: "Hablar con la IA por voz en vez de texto."
  },
  {
    icon: Layers,
    label: "Flashcards",
    description: "Generar tarjetas de repaso a partir de los temas."
  }
] as const;

export function ToolsPanel({
  collapsed,
  onToggleCollapsed,
  projectId,
  topics,
  latestStudyResult
}: ToolsPanelProps) {
  if (collapsed) {
    return (
      <aside className="panel flex h-14 w-full items-center justify-between rounded-lg px-3 md:h-full md:w-14 md:flex-col md:justify-start md:gap-4 md:py-4">
        <Wand2 size={18} className="text-violet-300" />
        <button
          type="button"
          onClick={onToggleCollapsed}
          className="grid h-9 w-9 place-items-center rounded-md border border-slate-800 text-slate-300 transition hover:border-violet-300/60 hover:text-white"
          aria-label="Mostrar panel de herramientas"
        >
          <ChevronsLeft size={16} className="hidden rotate-180 md:block" />
          <ChevronLeft size={16} className="rotate-180 md:hidden" />
        </button>
      </aside>
    );
  }

  return (
    <aside className="panel flex h-[420px] min-h-0 flex-col rounded-lg md:h-full md:w-72">
      <div className="flex items-center justify-between gap-3 border-b border-slate-800/80 p-4">
        <div className="flex items-center gap-2">
          <Wand2 size={18} className="text-violet-300" />
          <h2 className="text-sm font-semibold uppercase tracking-[0.16em] text-slate-300">
            Herramientas
          </h2>
        </div>
        <button
          type="button"
          onClick={onToggleCollapsed}
          className="grid h-7 w-7 place-items-center rounded-md border border-slate-800 text-slate-400 transition hover:border-violet-300/60 hover:text-white"
          aria-label="Ocultar panel de herramientas"
        >
          <ChevronsRight size={14} />
        </button>
      </div>

      <div className="thin-scrollbar min-h-0 flex-1 space-y-4 overflow-y-auto p-3">
        {latestStudyResult ? (
          <div>
            <p className="mb-2 flex items-center gap-2 text-xs uppercase tracking-[0.14em] text-slate-500">
              <BookMarked size={13} />
              Actividad reciente
            </p>
            <div className="rounded-lg border border-slate-800 bg-slate-950/35 p-3">
              <h3 className="text-sm font-medium text-white">{latestStudyResult.title}</h3>
              <p className="mt-1 line-clamp-3 text-xs leading-5 text-slate-400">
                {latestStudyResult.content}
              </p>
            </div>
          </div>
        ) : null}

        <div>
          <p className="mb-2 flex items-center gap-2 text-xs uppercase tracking-[0.14em] text-slate-500">
            <HelpCircle size={13} />
            Quiz
          </p>
          <QuizPanel projectId={projectId} topics={topics} />
        </div>

        {PLACEHOLDER_TOOLS.map((tool) => (
          <div
            key={tool.label}
            className="relative rounded-lg border border-slate-800 bg-slate-950/35 p-3 opacity-70"
          >
            <span className="absolute right-2 top-2 rounded-full border border-slate-700 bg-slate-900 px-2 py-0.5 text-[10px] uppercase tracking-wide text-slate-400">
              Proximamente
            </span>
            <div className="flex items-start gap-3 pr-16">
              <div className="mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-md border border-slate-700 text-violet-300">
                <tool.icon size={15} />
              </div>
              <div className="min-w-0">
                <h3 className="text-sm font-medium text-white">{tool.label}</h3>
                <p className="mt-1 text-xs leading-5 text-slate-400">{tool.description}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </aside>
  );
}
