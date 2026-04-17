import { useState, useEffect, useRef, useCallback } from "react";
import type { Update } from "@tauri-apps/plugin-updater";

export type UpdateStatus = "idle" | "checking" | "available" | "downloading" | "ready" | "error";

export interface UpdateState {
  status: UpdateStatus;
  version: string;
  progress: number;
  error: string;
}

const SKIPPED_KEY = "app_skipped_version";
const LAST_CHECK_KEY = "app_last_check";
const CHECK_INTERVAL_MS = 60 * 60 * 1000; // 1 hour

function getSkipped(): string {
  return localStorage.getItem(SKIPPED_KEY) ?? "";
}

function getLastCheck(): number {
  return Number(localStorage.getItem(LAST_CHECK_KEY)) || 0;
}

export function useUpdater() {
  const [state, setState] = useState<UpdateState>({
    status: "idle",
    version: "",
    progress: 0,
    error: "",
  });

  const candidateRef = useRef<Update | null>(null);
  const checkingRef = useRef(false);

  const check = useCallback(async () => {
    if (checkingRef.current) return;
    checkingRef.current = true;

    try {
      setState((s) => ({ ...s, status: "checking", error: "" }));

      const { check: checkUpdate } = await import("@tauri-apps/plugin-updater");
      const update = await checkUpdate();

      if (!update) {
        setState({ status: "idle", version: "", progress: 0, error: "" });
        localStorage.setItem(LAST_CHECK_KEY, String(Date.now()));
        return;
      }

      if (update.version === getSkipped()) {
        setState({ status: "idle", version: "", progress: 0, error: "" });
        localStorage.setItem(LAST_CHECK_KEY, String(Date.now()));
        return;
      }

      candidateRef.current = update;
      setState({
        status: "available",
        version: update.version,
        progress: 0,
        error: "",
      });
      localStorage.setItem(LAST_CHECK_KEY, String(Date.now()));
    } catch (e) {
      setState({
        status: "error",
        version: "",
        progress: 0,
        error: e instanceof Error ? e.message : String(e),
      });
    } finally {
      checkingRef.current = false;
    }
  }, []);

  const download = useCallback(async () => {
    const candidate = candidateRef.current;
    if (!candidate) return;

    try {
      setState((s) => ({ ...s, status: "downloading", progress: 0, error: "" }));

      let downloaded = 0;
      let contentLength = 0;

      await candidate.download((event) => {
        if (event.event === "Started") {
          contentLength = event.data.contentLength ?? 0;
          setState((s) => ({ ...s, progress: 0 }));
        } else if (event.event === "Progress") {
          downloaded += event.data.chunkLength;
          const pct =
            contentLength > 0
              ? Math.min(100, Math.round((downloaded / contentLength) * 100))
              : Math.min(95, (typeof state.progress === "number" ? state.progress : 0) + 1);
          setState((s) => ({ ...s, progress: pct }));
        }
      });

      setState((s) => ({ ...s, status: "ready", progress: 100 }));
    } catch (e) {
      setState({
        status: "error",
        version: state.version,
        progress: 0,
        error: e instanceof Error ? e.message : String(e),
      });
    }
  }, [state.progress]);

  const apply = useCallback(async () => {
    const candidate = candidateRef.current;
    if (!candidate) return;
    try {
      await candidate.install();
      const { relaunch } = await import("@tauri-apps/plugin-process");
      await relaunch();
    } catch (e) {
      setState((s) => ({
        ...s,
        status: "error",
        error: e instanceof Error ? e.message : String(e),
      }));
    }
  }, []);

  const skip = useCallback(() => {
    if (state.version) {
      localStorage.setItem(SKIPPED_KEY, state.version);
    }
    setState({ status: "idle", version: "", progress: 0, error: "" });
    candidateRef.current = null;
  }, [state.version]);

  const dismiss = useCallback(() => {
    setState({ status: "idle", version: "", progress: 0, error: "" });
  }, []);

  // Auto-check on mount + hourly interval
  useEffect(() => {
    const lastCheck = getLastCheck();
    const elapsed = Date.now() - lastCheck;

    if (elapsed >= CHECK_INTERVAL_MS) {
      check();
    } else {
      const timer = setTimeout(check, CHECK_INTERVAL_MS - elapsed);
      return () => clearTimeout(timer);
    }

    const interval = setInterval(check, CHECK_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [check]);

  return { state, check, download, apply, skip, dismiss };
}
