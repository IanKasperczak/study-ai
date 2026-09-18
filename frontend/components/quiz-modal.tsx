"use client";

import { Check, RotateCcw, X } from "lucide-react";
import { MarkdownContent } from "@/components/markdown-content";
import { computeQuizScore } from "@/lib/quiz-utils";
import type { QuizSession } from "@/lib/types";

type QuizModalProps = {
  open: boolean;
  session: QuizSession | null;
  onClose: () => void;
  onAnswer: (questionIndex: number, optionIndex: number) => void;
  onSubmit: () => void;
};

export function QuizModal({ open, session, onClose, onAnswer, onSubmit }: QuizModalProps) {
  if (!open || !session) return null;

  const { questions, answers, graded } = session;
  const answeredCount = answers.filter((answer) => answer !== -1).length;
  const allAnswered = answeredCount === questions.length;
  const score = computeQuizScore(session);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4 backdrop-blur-sm">
      <div className="panel flex max-h-[85vh] w-full max-w-2xl flex-col rounded-lg">
        <div className="flex items-center justify-between gap-3 border-b border-slate-800/80 p-4">
          <div>
            <h2 className="text-base font-semibold text-white">Quiz</h2>
            <p className="mt-0.5 text-xs text-slate-400">
              {graded
                ? `Resultado: ${score} / ${questions.length}`
                : `${answeredCount} de ${questions.length} respondidas`}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="grid h-8 w-8 shrink-0 place-items-center rounded-md border border-slate-800 text-slate-400 transition hover:border-slate-600 hover:text-white"
            aria-label="Cerrar (podes continuar despues)"
          >
            <X size={16} />
          </button>
        </div>

        <div className="thin-scrollbar min-h-0 flex-1 space-y-4 overflow-y-auto p-4">
          {questions.map((question, questionIndex) => (
            <div
              key={questionIndex}
              className="rounded-lg border border-slate-800 bg-slate-950/35 p-4"
            >
              <p className="text-sm font-medium text-white">
                {questionIndex + 1}. {question.question}
              </p>
              <div className="mt-3 space-y-2">
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
                      onClick={() => onAnswer(questionIndex, optionIndex)}
                      disabled={graded}
                      className={`flex w-full items-center gap-3 rounded-md border px-3 py-2 text-left text-sm text-slate-200 transition disabled:cursor-default ${stateClass}`}
                    >
                      {graded && isCorrectOption ? (
                        <Check size={15} className="shrink-0 text-emerald-300" />
                      ) : graded && isSelected ? (
                        <X size={15} className="shrink-0 text-red-300" />
                      ) : isSelected ? (
                        <span className="grid h-3.5 w-3.5 shrink-0 place-items-center rounded-full border border-sky-300 bg-sky-300/20">
                          <span className="h-1.5 w-1.5 rounded-full bg-sky-300" />
                        </span>
                      ) : (
                        <span className="h-3.5 w-3.5 shrink-0 rounded-full border border-slate-600" />
                      )}
                      <span className="min-w-0">{option}</span>
                    </button>
                  );
                })}
              </div>
              {graded && question.explanation ? (
                <MarkdownContent
                  content={question.explanation}
                  className="mt-3 text-xs leading-5 text-slate-400"
                />
              ) : null}
            </div>
          ))}
        </div>

        <div className="border-t border-slate-800/80 p-4">
          {graded ? (
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-semibold text-white">
                Resultado final: {score} / {questions.length}
              </p>
              <button
                type="button"
                onClick={onClose}
                className="inline-flex h-9 items-center gap-2 rounded-md border border-slate-700 px-3 text-sm text-slate-200 transition hover:border-sky-300/50"
              >
                <RotateCcw size={14} />
                Cerrar
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={onSubmit}
              disabled={!allAnswered}
              className="inline-flex h-10 w-full items-center justify-center gap-2 rounded-md bg-emerald-300 text-sm font-semibold text-slate-950 transition hover:bg-emerald-200 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Corregir
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
