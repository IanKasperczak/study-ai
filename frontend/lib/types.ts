export type FileSummary = {
  filename: string;
  content_type: string;
  character_count: number;
  status: string;
};

export type Topic = {
  id: string;
  title: string;
  description: string;
  keywords: string[];
  chunk_ids: string[];
};

export type ProjectResponse = {
  project_id: string;
  files: FileSummary[];
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

