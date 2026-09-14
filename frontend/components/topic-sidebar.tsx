"use client";

import {
  Check,
  ChevronDown,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  FileText,
  Layers3,
  Minus,
  Sparkles
} from "lucide-react";
import { type ReactNode, useState } from "react";
import type { DocumentFile, Topic } from "@/lib/types";

type TopicNode = Topic & { children: TopicNode[] };

type TopicSidebarProps = {
  documents: DocumentFile[];
  topics: Topic[];
  selectedTopicIds: string[];
  onToggleTopics: (topicIds: string[]) => void;
  onSelectAll: () => void;
  collapsed: boolean;
  onToggleCollapsed: () => void;
  footer?: ReactNode;
};

function buildTree(topics: Topic[]): TopicNode[] {
  const byId = new Map<string, TopicNode>();
  topics.forEach((topic) => byId.set(topic.id, { ...topic, children: [] }));

  const roots: TopicNode[] = [];
  byId.forEach((node) => {
    const parent = node.parent_id ? byId.get(node.parent_id) : undefined;
    if (parent) {
      parent.children.push(node);
    } else {
      roots.push(node);
    }
  });

  const byOrder = (a: TopicNode, b: TopicNode) => a.order - b.order;
  byId.forEach((node) => node.children.sort(byOrder));
  roots.sort(byOrder);
  return roots;
}

function collectIds(node: TopicNode): string[] {
  return [node.id, ...node.children.flatMap(collectIds)];
}

function selectionState(ids: string[], selectedTopicIds: string[]): "all" | "some" | "none" {
  const selectedCount = ids.reduce((count, id) => count + (selectedTopicIds.includes(id) ? 1 : 0), 0);
  if (selectedCount === 0) return "none";
  if (selectedCount === ids.length) return "all";
  return "some";
}

export function TopicSidebar({
  documents,
  topics,
  selectedTopicIds,
  onToggleTopics,
  onSelectAll,
  collapsed,
  onToggleCollapsed,
  footer
}: TopicSidebarProps) {
  const [expanded, setExpanded] = useState<Set<string>>(
    () => new Set(documents.map((doc) => `doc:${doc.id}`))
  );

  function toggleExpanded(key: string) {
    setExpanded((current) => {
      const next = new Set(current);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  }

  if (collapsed) {
    return (
      <aside className="panel flex h-14 w-full items-center justify-between rounded-lg px-3 md:h-full md:w-14 md:flex-col md:justify-start md:gap-4 md:py-4">
        <Layers3 size={18} className="text-sky-300" />
        <button
          type="button"
          onClick={onToggleCollapsed}
          className="grid h-9 w-9 place-items-center rounded-md border border-slate-800 text-slate-300 transition hover:border-sky-300/60 hover:text-white"
          aria-label="Mostrar panel de temas"
        >
          <ChevronsRight size={16} className="hidden md:block" />
          <ChevronRight size={16} className="md:hidden" />
        </button>
      </aside>
    );
  }

  return (
    <aside className="panel flex h-[320px] min-h-0 flex-col rounded-lg md:h-full">
      <div className="border-b border-slate-800/80 p-4">
        <div className="mb-3 flex items-center gap-2 text-slate-300">
          <Sparkles size={16} className="text-violet-300" />
          <span className="text-sm font-semibold text-white">Study IA</span>
        </div>
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Layers3 size={18} className="text-sky-300" />
            <h2 className="text-sm font-semibold uppercase tracking-[0.16em] text-slate-300">
              Temas
            </h2>
          </div>
          <div className="flex items-center gap-2">
            <span className="rounded-md bg-slate-800 px-2 py-1 text-xs text-slate-300">
              {topics.length}
            </span>
            <button
              type="button"
              onClick={onToggleCollapsed}
              className="grid h-7 w-7 place-items-center rounded-md border border-slate-800 text-slate-400 transition hover:border-sky-300/60 hover:text-white"
              aria-label="Ocultar panel de temas"
            >
              <ChevronsLeft size={14} />
            </button>
          </div>
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

      <div className="thin-scrollbar min-h-0 flex-1 space-y-1 overflow-y-auto p-3">
        {documents.length ? (
          documents.map((doc) => {
            const docTopics = topics.filter((topic) => topic.document_id === doc.id);
            const tree = buildTree(docTopics);
            const docIds = docTopics.map((topic) => topic.id);
            const docKey = `doc:${doc.id}`;
            const docExpanded = expanded.has(docKey);
            const docState = selectionState(docIds, selectedTopicIds);

            return (
              <div key={doc.id}>
                <div
                  className={`flex w-full items-center gap-2 rounded-lg border p-2.5 text-left transition ${
                    docState === "none"
                      ? "border-slate-800 bg-slate-950/35"
                      : "border-slate-700 bg-slate-900/50"
                  }`}
                >
                  <button
                    type="button"
                    onClick={() => toggleExpanded(docKey)}
                    disabled={!docIds.length}
                    className="grid h-6 w-6 shrink-0 place-items-center rounded text-slate-500 transition hover:text-slate-200 disabled:opacity-30"
                    aria-label={docExpanded ? "Colapsar archivo" : "Expandir archivo"}
                  >
                    {docIds.length ? (
                      docExpanded ? (
                        <ChevronDown size={15} />
                      ) : (
                        <ChevronRight size={15} />
                      )
                    ) : null}
                  </button>
                  <button
                    type="button"
                    onClick={() => docIds.length && onToggleTopics(docIds)}
                    disabled={!docIds.length}
                    className="flex min-w-0 flex-1 items-center gap-2 text-left disabled:cursor-not-allowed"
                  >
                    <SelectionIcon state={docState} tone="file" />
                    <FileText size={14} className="shrink-0 text-slate-400" />
                    <span className="truncate text-sm font-medium text-white">{doc.filename}</span>
                  </button>
                </div>

                {docExpanded ? (
                  <div className="mt-1 space-y-1">
                    {tree.map((node) => (
                      <TopicNodeRow
                        key={node.id}
                        node={node}
                        depth={1}
                        selectedTopicIds={selectedTopicIds}
                        expanded={expanded}
                        onToggleExpand={toggleExpanded}
                        onToggleSelect={onToggleTopics}
                      />
                    ))}
                  </div>
                ) : null}
              </div>
            );
          })
        ) : (
          <div className="rounded-lg border border-dashed border-slate-700 p-4 text-sm text-slate-400">
            No hay temas cargados.
          </div>
        )}
      </div>

      {footer}
    </aside>
  );
}

function TopicNodeRow({
  node,
  depth,
  selectedTopicIds,
  expanded,
  onToggleExpand,
  onToggleSelect
}: {
  node: TopicNode;
  depth: number;
  selectedTopicIds: string[];
  expanded: Set<string>;
  onToggleExpand: (key: string) => void;
  onToggleSelect: (ids: string[]) => void;
}) {
  const hasChildren = node.children.length > 0;
  const isExpanded = expanded.has(node.id);
  const ids = collectIds(node);
  const state = selectionState(ids, selectedTopicIds);

  return (
    <div>
      <div
        style={{ paddingLeft: 8 + depth * 14 }}
        className={`flex w-full items-start gap-2 rounded-lg border p-2 text-left transition ${
          state === "none"
            ? "border-slate-800 bg-slate-950/25 hover:border-slate-600"
            : "border-sky-300/50 bg-sky-300/5"
        }`}
      >
        <button
          type="button"
          onClick={() => onToggleExpand(node.id)}
          disabled={!hasChildren}
          className="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded text-slate-500 transition hover:text-slate-200 disabled:opacity-0"
          aria-label={isExpanded ? "Colapsar subtema" : "Expandir subtema"}
        >
          {hasChildren ? isExpanded ? <ChevronDown size={13} /> : <ChevronRight size={13} /> : null}
        </button>
        <button
          type="button"
          onClick={() => onToggleSelect(ids)}
          className="flex min-w-0 flex-1 items-start gap-2 text-left"
        >
          <SelectionIcon state={state} tone="topic" />
          <div className="min-w-0">
            <h3 className="line-clamp-2 text-sm font-medium text-white">{node.title}</h3>
            {node.description ? (
              <p className="mt-0.5 line-clamp-2 text-xs leading-5 text-slate-400">
                {node.description}
              </p>
            ) : null}
          </div>
        </button>
      </div>

      {hasChildren && isExpanded ? (
        <div className="mt-1 space-y-1">
          {node.children.map((child) => (
            <TopicNodeRow
              key={child.id}
              node={child}
              depth={depth + 1}
              selectedTopicIds={selectedTopicIds}
              expanded={expanded}
              onToggleExpand={onToggleExpand}
              onToggleSelect={onToggleSelect}
            />
          ))}
        </div>
      ) : null}
    </div>
  );
}

function SelectionIcon({ state, tone }: { state: "all" | "some" | "none"; tone: "file" | "topic" }) {
  const base = "mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-md border";
  if (state === "all") {
    return (
      <div className={`${base} border-sky-300 bg-sky-300 text-slate-950`}>
        <Check size={14} />
      </div>
    );
  }
  if (state === "some") {
    return (
      <div className={`${base} border-sky-300/70 bg-sky-300/20 text-sky-200`}>
        <Minus size={14} />
      </div>
    );
  }
  return (
    <div className={`${base} border-slate-700 text-slate-600`}>
      {tone === "file" ? <FileText size={12} /> : null}
    </div>
  );
}
