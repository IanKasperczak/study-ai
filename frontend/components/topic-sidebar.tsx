"use client";

import { BookOpen, Check, Layers3 } from "lucide-react";
import type { Topic } from "@/lib/types";

type TopicSidebarProps = {
  topics: Topic[];
  selectedTopicIds: string[];
  onToggleTopic: (topicId: string) => void;
  onSelectAll: () => void;
};

export function TopicSidebar({
  topics,
  selectedTopicIds,
  onToggleTopic,
  onSelectAll
}: TopicSidebarProps) {
  return (
    <aside className="panel flex h-[260px] min-h-0 flex-col rounded-lg md:h-full">
      <div className="border-b border-slate-800/80 p-4">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Layers3 size={18} className="text-sky-300" />
            <h2 className="text-sm font-semibold uppercase tracking-[0.16em] text-slate-300">
              Temas
            </h2>
          </div>
          <span className="rounded-md bg-slate-800 px-2 py-1 text-xs text-slate-300">
            {topics.length}
          </span>
        </div>
        <button
          type="button"
          onClick={onSelectAll}
          disabled={!topics.length}
          className="mt-3 inline-flex h-9 w-full items-center justify-center gap-2 rounded-md border border-slate-700 text-sm text-slate-200 transition hover:border-emerald-300/60 hover:text-emerald-100 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Check size={15} />
          Todos
        </button>
      </div>

      <div className="thin-scrollbar min-h-0 flex-1 space-y-2 overflow-y-auto p-3">
        {topics.length ? (
          topics.map((topic) => {
            const selected = selectedTopicIds.includes(topic.id);
            return (
              <button
                key={topic.id}
                type="button"
                onClick={() => onToggleTopic(topic.id)}
                className={`w-full rounded-lg border p-3 text-left transition ${
                  selected
                    ? "border-sky-300/60 bg-sky-300/10 shadow-glow"
                    : "border-slate-800 bg-slate-950/35 hover:border-slate-600"
                }`}
              >
                <div className="flex items-start gap-3">
                  <div
                    className={`mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-md border ${
                      selected
                        ? "border-sky-300 bg-sky-300 text-slate-950"
                        : "border-slate-700 text-slate-500"
                    }`}
                  >
                    {selected ? <Check size={14} /> : <BookOpen size={14} />}
                  </div>
                  <div className="min-w-0">
                    <h3 className="line-clamp-2 text-sm font-medium text-white">{topic.title}</h3>
                    <p className="mt-1 line-clamp-2 text-xs leading-5 text-slate-400">
                      {topic.description}
                    </p>
                  </div>
                </div>
              </button>
            );
          })
        ) : (
          <div className="rounded-lg border border-dashed border-slate-700 p-4 text-sm text-slate-400">
            No hay temas cargados.
          </div>
        )}
      </div>
    </aside>
  );
}
