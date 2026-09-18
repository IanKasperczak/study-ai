export type DocumentFile = {
  id: string;
  filename: string;
  content_type: string;
  character_count: number;
  word_count: number;
  status: string;
  error?: string | null;
};

export type Topic = {
  id: string;
  title: string;
  description: string;
  parent_id?: string | null;
  order: number;
  document_id: string;
  chunk_ids: string[];
};

export type ProjectResponse = {
  project_id: string;
  documents: DocumentFile[];
  topics: Topic[];
  total_chunks: number;
};

export type StudyActionResponse = {
  title: string;
  content: string;
  source_chunk_ids: string[];
};

export type SourceChunk = {
  id: string;
  source: string;
  preview: string;
};

export type ChatResponse = {
  answer: string;
  sources: SourceChunk[];
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: SourceChunk[];
};

export type QuizQuestion = {
  question: string;
  options: string[];
  correct_index: number;
  explanation: string;
};

export type GenerateQuizResponse = {
  topic_ids: string[];
  questions: QuizQuestion[];
};

export type QuizAttempt = {
  id: number;
  user_id: string;
  project_id: string;
  // Comma-joined topic ids (a quiz can span every topic selected in the
  // sidebar, not just one Subtema) -- split on "," to resolve titles.
  subtema_id: string;
  score: number;
  total_questions: number;
  created_at: string;
  // Full snapshot of the graded quiz, so history can reopen it for review
  // (right/wrong answers, explanations) without retaking it.
  questions: QuizQuestion[];
  answers: number[];
};

export type QuizSession = {
  topicIds: string[];
  questions: QuizQuestion[];
  answers: number[];
  graded: boolean;
};

