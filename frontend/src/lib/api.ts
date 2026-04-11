// API client — all calls to FastAPI backend
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  token?: string
): Promise<T> {
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "API Error");
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// ── Auth ──────────────────────────────────────────────────────────────────────
export const authApi = {
  register: (email: string, password: string, fullName?: string) =>
    apiFetch<{ id: string; email: string }>("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name: fullName }),
    }),

  login: (email: string, password: string) =>
    apiFetch<{ access_token: string; token_type: string }>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  me: (token: string) =>
    apiFetch<{ id: string; email: string; full_name: string }>("/api/v1/auth/me", {}, token),
};

// ── Interviews ────────────────────────────────────────────────────────────────
export interface Interview {
  id: string;
  topic: string;
  level: "junior" | "middle" | "senior";
  status: "pending" | "active" | "completed" | "failed";
  score?: number;
  report?: string;
  created_at: string;
  completed_at?: string;
  questions: Question[];
}

export interface Question {
  id: string;
  text: string;
  answer?: string;
  score?: number;
  feedback?: string;
  order: number;
  asked_at: string;
  answered_at?: string;
}

export const interviewApi = {
  create: (topic: string, level: string, token: string) =>
    apiFetch<Interview>("/api/v1/interviews", {
      method: "POST",
      body: JSON.stringify({ topic, level }),
    }, token),

  list: (token: string) =>
    apiFetch<Interview[]>("/api/v1/interviews", {}, token),

  get: (id: string, token: string) =>
    apiFetch<Interview>(`/api/v1/interviews/${id}`, {}, token),

  start: (id: string, token: string) =>
    apiFetch<Interview>(`/api/v1/interviews/${id}/start`, { method: "POST" }, token),

  submitAnswer: (id: string, questionId: string, answer: string, token: string) =>
    apiFetch<{ status: string }>(`/api/v1/interviews/${id}/answer`, {
      method: "POST",
      body: JSON.stringify({ question_id: questionId, answer }),
    }, token),

  delete: (id: string, token: string) =>
    apiFetch<void>(`/api/v1/interviews/${id}`, { method: "DELETE" }, token),
};

// ── Character coach ───────────────────────────────────────────────────────────
export const characterApi = {
  react: (
    question: string,
    answer: string,
    feedback: string,
    score: number,
    lang: "pl" | "ua",
    token: string,
  ) =>
    apiFetch<{ text: string }>("/api/v1/character/react", {
      method: "POST",
      body: JSON.stringify({ question, answer, feedback, score, lang }),
    }, token),
};
