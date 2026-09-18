import type {
  ChatResponse,
  GenerateQuizResponse,
  ProjectResponse,
  QuizAttempt,
  QuizQuestion,
  StudyActionResponse
} from "./types";
import { getUserId } from "./user-id";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  // Anonymous per-device id on every request (see lib/user-id.ts) -- no
  // login, just lets per-device data like quiz history persist.
  const headers = new Headers(init?.headers);
  headers.set("X-User-Id", getUserId());

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });
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
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export async function uploadStudyFiles(files: File[], projectId?: string): Promise<ProjectResponse> {
  const formData = new FormData();

  files.forEach((file) => {
    const relativePath = (file as File & { webkitRelativePath?: string }).webkitRelativePath;
    formData.append("files", file, relativePath || file.name);
  });

  const query = projectId ? `?project_id=${encodeURIComponent(projectId)}` : "";
  return request<ProjectResponse>(`/uploads${query}`, {
    method: "POST",
    body: formData
  });
}

export async function getProject(projectId: string): Promise<ProjectResponse> {
  return request<ProjectResponse>(`/uploads/${projectId}`);
}

export async function deleteDocument(projectId: string, documentId: string): Promise<ProjectResponse> {
  return request<ProjectResponse>(`/uploads/${projectId}/documents/${documentId}`, {
    method: "DELETE"
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

export async function generateQuiz(
  projectId: string,
  topicIds: string[],
  numQuestions = 10
): Promise<GenerateQuizResponse> {
  return request<GenerateQuizResponse>("/quiz/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ project_id: projectId, topic_ids: topicIds, num_questions: numQuestions })
  });
}

export async function saveQuizAttempt(
  projectId: string,
  topicIds: string[],
  score: number,
  totalQuestions: number,
  questions: QuizQuestion[],
  answers: number[]
): Promise<QuizAttempt> {
  return request<QuizAttempt>("/quiz/attempts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      project_id: projectId,
      topic_ids: topicIds,
      score,
      total_questions: totalQuestions,
      questions,
      answers
    })
  });
}

export async function getQuizAttempts(projectId: string): Promise<QuizAttempt[]> {
  return request<QuizAttempt[]>(`/quiz/attempts?project_id=${encodeURIComponent(projectId)}`);
}

export async function deleteQuizAttempt(attemptId: number): Promise<void> {
  await request<void>(`/quiz/attempts/${attemptId}`, { method: "DELETE" });
}
