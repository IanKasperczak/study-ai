"use client";

import { motion } from "framer-motion";
import { ChatPanel } from "@/components/chat-panel";
import { FileUploader } from "@/components/file-uploader";
import { PomodoroTimer } from "@/components/pomodoro-timer";
import { StarfieldBackground } from "@/components/starfield-background";
import { StudyActions } from "@/components/study-actions";
import { ToolsPanel } from "@/components/tools-panel";
import { TopicSidebar } from "@/components/topic-sidebar";
import { useLocalStore, writeLocalStore } from "@/lib/local-store";
import type { ProjectResponse, Topic } from "@/lib/types";
import { useMemo, useState } from "react";

const SIDEBAR_COLLAPSED_KEY = "study-ia-sidebar-collapsed";
const TOOLS_COLLAPSED_KEY = "study-ia-tools-collapsed";

// Tailwind's JIT scanner needs full literal class names in source, so the
// four collapse combinations are spelled out instead of built dynamically.
const GRID_TEMPLATES: Record<string, string> = {
  "0-0": "md:grid-cols-[72px_1fr_72px]",
  "0-1": "md:grid-cols-[72px_1fr_288px]",
  "1-0": "md:grid-cols-[320px_1fr_72px]",
  "1-1": "md:grid-cols-[320px_1fr_288px]"
};

export default function HomePage() {
  const [projectId, setProjectId] = useState<string | null>(null);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [selectedTopicIds, setSelectedTopicIds] = useState<string[]>([]);
  const [lastProject, setLastProject] = useState<ProjectResponse | null>(null);

  const sidebarCollapsed = useLocalStore(SIDEBAR_COLLAPSED_KEY, false);
  const toolsCollapsed = useLocalStore(TOOLS_COLLAPSED_KEY, true);

  const selectedTopicsLabel = useMemo(() => {
    if (!selectedTopicIds.length) return "Sin seleccion";
    return `${selectedTopicIds.length} de ${topics.length} temas`;
  }, [selectedTopicIds.length, topics.length]);

  const gridClass =
    GRID_TEMPLATES[`${sidebarCollapsed ? 0 : 1}-${toolsCollapsed ? 0 : 1}`];

  function handleProjectReady(project: ProjectResponse) {
    setProjectId(project.project_id);
    setTopics(project.topics);
    setSelectedTopicIds(project.topics.map((topic) => topic.id));
    setLastProject(project);
  }

  function toggleTopics(topicIds: string[]) {
    setSelectedTopicIds((current) => {
      const allSelected = topicIds.every((id) => current.includes(id));
      if (allSelected) {
        return current.filter((id) => !topicIds.includes(id));
      }
      const merged = new Set(current);
      topicIds.forEach((id) => merged.add(id));
      return Array.from(merged);
    });
  }

  function selectAllTopics() {
    setSelectedTopicIds((current) =>
      current.length === topics.length ? [] : topics.map((topic) => topic.id)
    );
  }

  return (
    <main className="night-sky relative min-h-screen overflow-hidden p-4 text-slate-100 md:p-6">
      <StarfieldBackground />

      <div
        className={`relative z-10 mx-auto grid h-[calc(100vh-2rem)] max-w-[100rem] grid-cols-1 gap-4 md:h-[calc(100vh-3rem)] ${gridClass}`}
      >
        <TopicSidebar
          documents={lastProject?.documents ?? []}
          topics={topics}
          selectedTopicIds={selectedTopicIds}
          onToggleTopics={toggleTopics}
          onSelectAll={selectAllTopics}
          collapsed={sidebarCollapsed}
          onToggleCollapsed={() => writeLocalStore(SIDEBAR_COLLAPSED_KEY, !sidebarCollapsed)}
          footer={<FileUploader onProjectReady={handleProjectReady} />}
        />

        <motion.section
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35 }}
          className="thin-scrollbar flex min-h-0 flex-col gap-4 overflow-y-auto pb-36 md:pb-28"
        >
          {lastProject ? (
            <section className="panel rounded-lg p-4">
              <div className="grid gap-3 text-sm text-slate-300 sm:grid-cols-3">
                <div>
                  <p className="text-xs uppercase tracking-[0.16em] text-slate-500">Archivos</p>
                  <p className="mt-1 font-semibold text-white">{lastProject.documents.length}</p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-[0.16em] text-slate-500">Chunks</p>
                  <p className="mt-1 font-semibold text-white">{lastProject.total_chunks}</p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-[0.16em] text-slate-500">Seleccion</p>
                  <p className="mt-1 font-semibold text-white">{selectedTopicsLabel}</p>
                </div>
              </div>
            </section>
          ) : null}

          <StudyActions projectId={projectId} selectedTopicIds={selectedTopicIds} />
          <ChatPanel projectId={projectId} selectedTopicIds={selectedTopicIds} />
        </motion.section>

        <ToolsPanel
          collapsed={toolsCollapsed}
          onToggleCollapsed={() => writeLocalStore(TOOLS_COLLAPSED_KEY, !toolsCollapsed)}
        />
      </div>

      <PomodoroTimer />
    </main>
  );
}
