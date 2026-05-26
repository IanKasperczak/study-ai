"use client";

import { motion } from "framer-motion";
import { ChatPanel } from "@/components/chat-panel";
import { FileUploader } from "@/components/file-uploader";
import { PomodoroTimer } from "@/components/pomodoro-timer";
import { StudyActions } from "@/components/study-actions";
import { TopicSidebar } from "@/components/topic-sidebar";
import type { ProjectResponse, Topic } from "@/lib/types";
import { useMemo, useState } from "react";

export default function HomePage() {
  const [projectId, setProjectId] = useState<string | null>(null);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [selectedTopicIds, setSelectedTopicIds] = useState<string[]>([]);
  const [lastProject, setLastProject] = useState<ProjectResponse | null>(null);

  const selectedTopicsLabel = useMemo(() => {
    if (!selectedTopicIds.length) return "Sin seleccion";
    return `${selectedTopicIds.length} de ${topics.length} temas`;
  }, [selectedTopicIds.length, topics.length]);

  function handleProjectReady(project: ProjectResponse) {
    setProjectId(project.project_id);
    setTopics(project.topics);
    setSelectedTopicIds(project.topics.map((topic) => topic.id));
    setLastProject(project);
  }

  function toggleTopic(topicId: string) {
    setSelectedTopicIds((current) =>
      current.includes(topicId)
        ? current.filter((id) => id !== topicId)
        : [...current, topicId]
    );
  }

  function selectAllTopics() {
    setSelectedTopicIds((current) =>
      current.length === topics.length ? [] : topics.map((topic) => topic.id)
    );
  }

  return (
    <main className="night-sky star-field min-h-screen overflow-hidden p-4 text-slate-100 md:p-6">
      <div className="relative z-10 mx-auto grid h-[calc(100vh-2rem)] max-w-7xl grid-cols-1 gap-4 md:h-[calc(100vh-3rem)] md:grid-cols-[320px_1fr]">
        <TopicSidebar
          topics={topics}
          selectedTopicIds={selectedTopicIds}
          onToggleTopic={toggleTopic}
          onSelectAll={selectAllTopics}
        />

        <motion.section
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35 }}
          className="thin-scrollbar flex min-h-0 flex-col gap-4 overflow-y-auto pb-36 md:pb-28"
        >
          <FileUploader onProjectReady={handleProjectReady} />

          {lastProject ? (
            <section className="panel rounded-lg p-4">
              <div className="grid gap-3 text-sm text-slate-300 sm:grid-cols-3">
                <div>
                  <p className="text-xs uppercase tracking-[0.16em] text-slate-500">Archivos</p>
                  <p className="mt-1 font-semibold text-white">{lastProject.files.length}</p>
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
      </div>

      <PomodoroTimer />
    </main>
  );
}

