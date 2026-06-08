// Typed fetch wrapper for the backend REST API.
// All calls go over the Tailscale network; the base URL is injected via env.

import type {
  ChatMessage,
  ChatResponse,
  Commit,
  CommitPage,
  Feedback,
  Library,
  OverviewStats,
  Project,
  SessionSummary,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    // Dashboard data is live; never serve stale.
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`API ${res.status} on ${path}: ${await res.text()}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  listProjects: () => request<Project[]>("/projects"),
  getProject: (id: string) => request<Project>(`/projects/${id}`),
  createProject: (body: { name: string; gdrive_folder_id: string; description?: string }) =>
    request<Project>("/projects", { method: "POST", body: JSON.stringify(body) }),

  listSessions: (projectId?: string) =>
    request<SessionSummary[]>(
      `/sessions${projectId ? `?project_id=${encodeURIComponent(projectId)}` : ""}`,
    ),
  getSession: (id: string) => request<SessionSummary>(`/sessions/${id}`),

  listCommits: (sessionId: string, cursor?: string) =>
    request<CommitPage>(
      `/sessions/${sessionId}/commits${cursor ? `?cursor=${encodeURIComponent(cursor)}` : ""}`,
    ),

  listFeedback: (sessionId: string) =>
    request<Feedback[]>(`/sessions/${sessionId}/feedback`),

  submitFeedback: (sessionId: string, comment: string) =>
    request<Feedback>(`/sessions/${sessionId}/feedback`, {
      method: "POST",
      body: JSON.stringify({ comment }),
    }),

  approve: (sessionId: string) =>
    request<{ session_id: string; session_state: string }>(`/sessions/${sessionId}/approve`, {
      method: "POST",
    }),

  getArtifact: (fileId: string) =>
    request<{ gdrive_file_id: string; content: string }>(`/artifacts/${fileId}`),

  listLibrary: (projectId: string) =>
    request<Library>(`/projects/${projectId}/library`),

  getOverview: () => request<OverviewStats>("/stats/overview"),

  chatArtifact: (fileId: string, messages: ChatMessage[], currentMarkdown: string) =>
    request<ChatResponse>(`/artifacts/${fileId}/chat`, {
      method: "POST",
      body: JSON.stringify({ messages, current_markdown: currentMarkdown }),
    }),

  updateArtifact: (fileId: string, content: string) =>
    request<{ gdrive_file_id: string; drive_revision_id: string }>(`/artifacts/${fileId}`, {
      method: "PATCH",
      body: JSON.stringify({ content }),
    }),
};

export type {
  Commit,
  CommitPage,
  Feedback,
  Library,
  OverviewStats,
  Project,
  SessionSummary,
};
