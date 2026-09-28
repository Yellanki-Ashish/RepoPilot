import { createContext, createElement, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import {
  analyzeRepository, deleteRepository, describeError, getProgress, getRepository,
} from "../api/api";

const RepositoryContext = createContext(null);
const STORAGE_KEY = "repopilot:last_repository";

const newProgressId = () => `p${Date.now().toString(36)}${Math.random().toString(36).slice(2, 10)}`;

export function RepositoryProvider({ children }) {
  const [repo, setRepo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState({ step: 0, message: "" });
  const [error, setError] = useState("");
  const pollRef = useRef(null);

  const stopPolling = () => {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = null;
  };

  // Restore the last analysed repository after a page refresh
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (!saved) return;
    getRepository(saved).then(setRepo).catch(() => localStorage.removeItem(STORAGE_KEY));
  }, []);

  useEffect(() => stopPolling, []);

  const analyze = useCallback(async (url, forceRefresh = false) => {
    setLoading(true);
    setError("");
    setProgress({ step: 0, message: "Scanning repository..." });
    const progressId = newProgressId();
    stopPolling();
    pollRef.current = setInterval(async () => {
      try {
        const p = await getProgress(progressId);
        if (p.status === "running") setProgress({ step: p.step, message: p.message });
      } catch {
        /* polling is cosmetic; ignore failures */
      }
    }, 1000);
    try {
      const data = await analyzeRepository(url, { progressId, forceRefresh });
      setRepo(data);
      localStorage.setItem(STORAGE_KEY, data.repository_id);
      return data;
    } catch (err) {
      setError(describeError(err, "Repository analysis failed. Check backend logs."));
      return null;
    } finally {
      stopPolling();
      setLoading(false);
    }
  }, []);

  const load = useCallback(async (repositoryId) => {
    setLoading(true);
    setError("");
    try {
      const data = await getRepository(repositoryId);
      setRepo(data);
      localStorage.setItem(STORAGE_KEY, data.repository_id);
      return data;
    } catch (err) {
      setError(describeError(err, "Could not load the repository."));
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const remove = useCallback(async () => {
    if (!repo) return;
    try {
      await deleteRepository(repo.repository_id);
      localStorage.removeItem(STORAGE_KEY);
      setRepo(null);
    } catch (err) {
      setError(describeError(err, "Could not delete the repository."));
    }
  }, [repo]);

  const value = useMemo(
    () => ({ repo, loading, progress, error, setError, analyze, load, remove }),
    [repo, loading, progress, error, analyze, load, remove],
  );
  return createElement(RepositoryContext.Provider, { value }, children);
}

export function useRepository() {
  const ctx = useContext(RepositoryContext);
  if (!ctx) throw new Error("useRepository must be used inside <RepositoryProvider>");
  return ctx;
}
