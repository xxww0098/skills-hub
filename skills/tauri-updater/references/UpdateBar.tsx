import { AnimatePresence, motion } from "framer-motion";
import { ArrowUpCircle, RefreshCw, CheckCircle2, AlertCircle, X } from "lucide-react";
import type { UpdateStatus } from "../hooks/useUpdater";

interface UpdateBarProps {
  status: UpdateStatus;
  version: string;
  progress: number;
  error: string;
  onUpdate?: () => void;
  onRestart?: () => void;
  onSkip?: () => void;
  onDismiss?: () => void;
}

export function UpdateBar({
  status,
  version,
  progress,
  error,
  onUpdate,
  onRestart,
  onSkip,
  onDismiss,
}: UpdateBarProps) {
  if (status === "idle" || status === "checking") return null;

  return (
    <motion.div
      initial={{ height: 0, opacity: 0 }}
      animate={{ height: "auto", opacity: 1 }}
      exit={{ height: 0, opacity: 0 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
      className="overflow-hidden border-b border-border-subtle"
    >
      {status === "available" && (
        <div className="px-4 py-2.5 bg-blue-500/8 flex flex-col gap-1.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <ArrowUpCircle className="w-3.5 h-3.5 text-blue-500" />
              <span className="text-xs font-medium text-foreground">v{version}</span>
              <span className="text-xs text-muted-foreground">available</span>
            </div>
            <button
              onClick={onDismiss}
              className="text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
            >
              <X className="w-3 h-3" />
            </button>
          </div>
          <div className="flex items-center gap-1.5">
            <button
              onClick={onUpdate}
              className="flex-1 text-xs bg-blue-500 text-white rounded px-2 py-1 hover:bg-blue-600 transition-colors cursor-pointer"
            >
              Update
            </button>
            <button
              onClick={onSkip}
              className="text-xs text-muted-foreground hover:text-foreground transition-colors px-1 cursor-pointer"
            >
              Skip
            </button>
          </div>
        </div>
      )}

      {status === "downloading" && (
        <div className="px-4 py-2.5 bg-muted/50">
          <div className="flex items-center gap-1.5 mb-1.5">
            <RefreshCw className="w-3.5 h-3.5 text-muted-foreground animate-spin" />
            <span className="text-xs text-muted-foreground">Downloading… {progress}%</span>
          </div>
          <div className="h-1 bg-border rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-primary rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.3 }}
            />
          </div>
        </div>
      )}

      {status === "ready" && (
        <div className="px-4 py-2.5 bg-emerald-500/8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
              <span className="text-xs text-muted-foreground">Ready</span>
            </div>
            <button
              onClick={onRestart}
              className="text-xs bg-emerald-500 text-white rounded px-2.5 py-1 hover:bg-emerald-600 transition-colors cursor-pointer"
            >
              Restart
            </button>
          </div>
        </div>
      )}

      {status === "error" && (
        <div className="px-4 py-2.5 bg-red-500/8">
          <div className="flex items-center gap-1.5 mb-1">
            <AlertCircle className="w-3.5 h-3.5 text-red-500" />
            <span className="text-xs text-red-600 truncate" title={error}>
              {error.length > 25 ? error.slice(0, 25) + "…" : error}
            </span>
          </div>
          <button
            onClick={onUpdate}
            className="text-xs text-red-500 hover:text-red-600 transition-colors cursor-pointer"
          >
            Retry
          </button>
        </div>
      )}
    </motion.div>
  );
}

// Usage inside Sidebar:
// <AnimatePresence>
//   {updateStatus && updateStatus !== "idle" && updateStatus !== "checking" && (
//     <UpdateBar
//       status={updateStatus}
//       version={updateVersion ?? ""}
//       progress={updateProgress ?? 0}
//       error={updateError ?? ""}
//       onUpdate={onUpdate}
//       onRestart={onRestart}
//       onSkip={onSkip}
//       onDismiss={onDismiss}
//     />
//   )}
// </AnimatePresence>
