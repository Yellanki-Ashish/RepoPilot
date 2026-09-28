import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const http = axios.create({ baseURL: API_BASE_URL, timeout: 120000 });

/** Turn any axios error into a short, user-friendly message (never a stack trace). */
export function describeError(error, fallback = "Something went wrong. Check backend logs.") {
  if (!error.response) {
    return "Cannot reach the RepoPilot backend. Make sure it is running (uvicorn app.main:app --reload).";
  }
  const { status, data } = error.response;
  const detail = typeof data?.detail === "string" ? data.detail : null;
  if (status === 422) return "The request was invalid. Please check your input.";
  if (status === 500) return fallback;
  return detail || fallback;
}

// Repository analysis can take minutes (downloads + embeddings), so it has no timeout.
export const analyzeRepository = (url, { progressId, forceRefresh = false } = {}) =>
  http.post("/api/repository/analyze", { url, progress_id: progressId, force_refresh: forceRefresh },
    { timeout: 0 }).then((r) => r.data);

export const getProgress = (progressId) => http.get(`/api/progress/${progressId}`).then((r) => r.data);
export const getRepository = (repo) => http.get(`/api/repository/${repo}`).then((r) => r.data);
export const listRepositories = () => http.get("/api/repositories").then((r) => r.data.repositories);
export const searchRepository = (repository, query, topK) =>
  http.post("/api/repository/search", { repository, query, top_k: topK }).then((r) => r.data);
export const askAssistant = (repository, question, topK) =>
  http.post("/api/assistant/ask", { repository, question, top_k: topK }, { timeout: 600000 }).then((r) => r.data);
export const getGraph = (repo) => http.get(`/api/repository/${repo}/graph`).then((r) => r.data);
export const getComplexity = (repo) => http.get(`/api/repository/${repo}/complexity`).then((r) => r.data);
export const getArchitecture = (repo) => http.get(`/api/repository/${repo}/architecture`).then((r) => r.data);
export const getFile = (repo, path) =>
  http.get(`/api/repository/${repo}/file`, { params: { path } }).then((r) => r.data);
export const getRoadmap = (repository, includeAiSummary = true) =>
  http.post("/api/onboarding/roadmap", { repository, include_ai_summary: includeAiSummary },
    { timeout: 600000 }).then((r) => r.data);
export const getIssues = (repo, state = "open", limit = 20) =>
  http.get(`/api/issues/${repo}`, { params: { state, limit } }).then((r) => r.data);
export const analyzeIssue = (repository, issueNumber = null, limit = 10) =>
  http.post("/api/issues/analyze", { repository, issue_number: issueNumber, limit }).then((r) => r.data);
export const deleteRepository = (repo) => http.delete(`/api/repository/${repo}`).then((r) => r.data);
