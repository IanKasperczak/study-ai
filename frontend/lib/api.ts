import type { ChatResponse, ProjectResponse, StudyActionResponse } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const detail = await response.json().catch(() => null);
    throw new Error(detail?.detail ?? `Request failed with status ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function uploadStudyFiles(files: File[]): Promise<ProjectResponse> {
  const formData = new FormData();

  files.forEach((file) => {
    const relativePath = (file as File & { webkitRelativePath?: string }).webkitRelativePath;
    formData.append("files", file, relativePath || file.name);
  });

  const response = await fetch(`${API_BASE_URL}/uploads`, {
    method: "POST",
    body: formData
  });

  return parseResponse<ProjectResponse>(response);
}

export async function generateStudyAction(
  endpoint: "summary" | "simple-explanation",
  projectId: string,
  topicIds: string[]
): Promise<StudyActionResponse> {
  const response = await fetch(`${API_BASE_URL}/study/${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ project_id: projectId, topic_ids: topicIds })
  });

  return parseResponse<StudyActionResponse>(response);
}

export async function askContextualChat(
  projectId: string,
  message: string,
  topicIds: string[]
): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ project_id: projectId, message, topic_ids: topicIds })
  });

  return parseResponse<ChatResponse>(response);
}

