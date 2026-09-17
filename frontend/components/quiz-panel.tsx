"use client";

import { Check, HelpCircle, Loader2, RotateCcw, X } from "lucide-react";
import { useEffect, useState } from "react";
import { generateQuiz, getQuizAttempts, saveQuizAttempt } from "@/lib/api";
import type { QuizAttempt, QuizQuestion, Topic } from "@/lib/types";

type QuizPanelProps = {
  projectId: string | null;
  topics: Topic[];
};

export function QuizPanel({ projectId, topics }: QuizPanelProps) {
  const [selectedTopicId, setSelectedTopicId] = useState("");
  const [questions, setQuestions] = useState<QuizQuestion[] | null>(null);
  const [answers, setAnswers] = useState<number[]>([]);
  const [graded, setGraded] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [attempts, setAttempts] = useState<QuizAttempt[]>([]);

  useEffect(() => {
    getQuizAttempts()
      .then(setAttempts)
      .catch(() => {
        // History is a nice-to-have; a failed fetch shouldn't block the quiz itself.
      });
  }, []);

  const effectiveTopicId = selectedTopicId || topics[0]?.id || "";

  async function handleGenerate() {
    if (!projectId || !effectiveTopicId) return;

    setIsGenerating(true);
    setError(null);
    setQuestions(null);
    setGraded(false);

    try {
      const response = await generateQuiz(projectId, effectiveTopicId);
      setQuestions(response.questions);
      setAnswers(new Array(response.questions.length).fill(-1));
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo generar el quiz.");
    } finally {
      setIsGenerating(false);
    }
  }

  function selectAnswer(questionIndex: number, optionIndex: number) {
    if (graded) return;
    setAnswers((current) => {
      const next = [...current];
      next[questionIndex] = optionIndex;
      return next;
    });
  }

  const score = (questions ?? []).reduce(
    (total, question, index) => total + (answers[index] === question.correct_index ? 1 : 0),
    0
  );
  const allAnswered = questions !== null && answers.every((answer) => answer !== -1);

  async function handleSubmit() {
    if (!questions || !effectiveTopicId) return;
    setGraded(true);

    try {
      const attempt = await saveQuizAttempt(effectiveTopicId, score, questions.length);
      setAttempts((current) => [attempt, ...current]);
    } catch {
      // The graded view is already shown locally; losing history on a failed
      // save isn't worth blocking or confusing the user with an error here.
    }
  }

  function handleReset() {
    setQuestions(null);
    setAnswers([]);
    setGraded(false);
    setError(null);
  }

  function topicTitle(topicId: string): string {
    return topics.find((topic) => topic.id === topicId)?.title ?? topicId;
  }

  return (
    <div className="space-y-3">
      {!questions ? (
        <div className="space-y-2">
          <select
            value={effectiveTopicId}
            onChange={(event) => setSelectedTopicId(event.target.value)}
            disabled={!topics.length || isGenerating}
            className="h-9 w-full rounded-md border border-slate-700 bg-slate-900 px-2 text-sm text-slate-100 outline-none transition focus:border-sky-300/70 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {topics.length ? (
              topics.map((topic) => (
                <option key={topic.id} value={topic.id}>
                  {topic.title}
                </option>
              ))
            ) : (
              <option value="">No hay temas cargados</option>
            )}
          </select>
          <button
            type="button"
            onClick={handleGenerate}
            disabled={!projectId || !effectiveTopicId || isGenerating}
            className="inline-flex h-9 w-full items-center justify-center gap-2 rounded-md bg-emerald-300 text-sm font-semibold text-slate-950 transition hover:bg-emerald-200 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isGenerating ? <Loader2 size={15} className="animate-spin" /> : <HelpCircle size={15} />}
            Generar quiz
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {questions.map((question, questionIndex) => (
            <div key={questionIndex} className="rounded-lg border border-slate-800 bg-slate-950/35 p-3">
              <p className="text-sm font-medium text-white">
                {questionIndex + 1}. {question.question}
              </p>
              <div className="mt-2 space-y-1.5">
                {question.options.map((option, optionIndex) => {
                  const isSelected = answers[questionIndex] === optionIndex;
                  const isCorrectOption = question.correct_index === optionIndex;
                  let stateClass = "border-slate-800 bg-slate-950/40 hover:border-slate-600";
                  if (graded && isCorrectOption) {
                    stateClass = "border-emerald-300/60 bg-emerald-300/10";
                  } else if (graded && isSelected && !isCorrectOption) {
                    stateClass = "border-red-400/50 bg-red-950/30";
                  } else if (!graded && isSelected) {
                    stateClass = "border-sky-300/60 bg-sky-300/10";
                  }

                  return (
                    <button
                      key={optionIndex}
                      type="button"
                      onClick={() => selectAnswer(questionIndex, optionIndex)}
                      disabled={graded}
                      className={`flex w-full items-center gap-2 rounded-md border px-2.5 py-1.5 text-left text-xs text-slate-200 transition disabled:cursor-default ${stateClass}`}
                    >
                      {graded && isCorrectOption ? (
                        <Check size={13} className="shrink-0 text-emerald-300" />
                      ) : graded && isSelected ? (
                        <X size={13} className="shrink-0 text-red-300" />
                      ) : (
                        <span className="h-3 w-3 shrink-0 rounded-full border border-slate-600" />
                      )}
                      <span className="min-w-0">{option}</span>
                    </button>
                  );
                })}
              </div>
              {graded ? (
                <p className="mt-2 text-xs leading-5 text-slate-400">{question.explanation}</p>
              ) : null}
            </div>
          ))}

          {graded ? (
            <div className="rounded-lg border border-slate-700 bg-slate-900/50 p-3 text-center">
              <p className="text-sm font-semibold text-white">
                Resultado: {score} / {questions.length}
              </p>
              <button
                type="button"
                onClick={handleReset}
                className="mt-2 inline-flex h-8 items-center gap-2 rounded-md border border-slate-700 px-3 text-xs text-slate-200 transition hover:border-sky-300/50"
              >
                <RotateCcw size={13} />
                Otro quiz
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={handleSubmit}
              disabled={!allAnswered}
              className="inline-flex h-9 w-full items-center justify-center gap-2 rounded-md bg-emerald-300 text-sm font-semibold text-slate-950 transition hover:bg-emerald-200 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Corregir
            </button>
          )}
        </div>
      )}

      {error ? (
        <div className="rounded-md border border-red-400/30 bg-red-950/35 px-3 py-2 text-xs text-red-100">
          {error}
        </div>
      ) : null}

      {attempts.length ? (
        <div className="border-t border-slate-800/80 pt-3">
          <p className="mb-2 text-xs uppercase tracking-[0.14em] text-slate-500">Historial</p>
          <div className="space-y-1.5">
            {attempts.slice(0, 5).map((attempt) => (
              <div
                key={attempt.id}
                className="flex items-center justify-between gap-2 rounded-md border border-slate-800 bg-slate-950/30 px-2.5 py-1.5 text-xs"
              >
                <span className="min-w-0 truncate text-slate-300">
                  {topicTitle(attempt.subtema_id)}
                </span>
                <span className="shrink-0 font-medium text-slate-200">
                  {attempt.score}/{attempt.total_questions}
                </span>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
