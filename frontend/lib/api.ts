import type { ChatResponse, ProjectResponse, StudyActionResponse } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, init);
  } catch (err) {
    if (err instanceof TypeError) {
      throw new Error(
        `No se pudo conectar con el backend en ${API_BASE_URL}${path}. ` +
          "Verifica que el servidor (uvicorn) este corriendo en el puerto correcto."
      );
    }
    throw err;
  }

  if (!response.ok) {
    const detail = await response.json().catch(() => null);
    throw new Error(
      detail?.detail ?? `El servidor respondio con el estado ${response.status}.`
    );
  }
  return response.json() as Promise<T>;
}

export async function uploadStudyFiles(files: File[]): Promise<ProjectResponse> {
  const formData = new FormData();

  files.forEach((file) => {
    const relativePath = (file as File & { webkitRelativePath?: string }).webkitRelativePath;
    formData.append("files", file, relativePath || file.name);
  });

  return request<ProjectResponse>("/uploads", {
    method: "POST",
    body: formData
  });
}

export async function generateStudyAction(
  endpoint: "summary" | "simple-explanation",
  projectId: string,
  topicIds: string[]
): Promise<StudyActionResponse> {
  return request<StudyActionResponse>(`/study/${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ project_id: projectId, topic_ids: topicIds })
  });
}

export async function askContextualChat(
  projectId: string,
  message: string,
  topicIds: string[]
): Promise<ChatResponse> {
  return request<ChatResponse>("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ project_id: projectId, message, topic_ids: topicIds })
  });
}