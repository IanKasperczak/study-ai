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

