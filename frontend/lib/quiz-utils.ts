import type { QuizSession } from "./types";

export function computeQuizScore(session: QuizSession): number {
  return session.questions.reduce(
    (total, question, index) => total + (session.answers[index] === question.correct_index ? 1 : 0),
    0
  );
}
