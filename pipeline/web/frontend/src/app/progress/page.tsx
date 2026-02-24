"use client";

import { useRouter } from "next/navigation";
import {
  Activity,
  CheckCircle2,
  XCircle,
  Square,
  Loader2,
  ArrowRight,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { usePipelineStatus } from "@/lib/hooks";
import { stopPipeline } from "@/lib/api";
import { PHASE_LABELS, RULE_DISPLAY_NAMES } from "@/lib/types";
import { cn } from "@/lib/utils";

const PIPELINE_PHASES = [
  "discovering",
  "batching",
  "aggregating",
  "cleaning",
  "done",
] as const;

function PhaseStep({
  phase,
  currentPhase,
  label,
}: {
  phase: string;
  currentPhase: string;
  label: string;
}) {
  const phases = PIPELINE_PHASES as readonly string[];
  const currentIdx = phases.indexOf(currentPhase);
  const thisIdx = phases.indexOf(phase);
  const isActive = phase === currentPhase;
  const isComplete = thisIdx < currentIdx;

  return (
    <div className="flex items-center gap-2">
      <div
        className={cn(
          "flex h-7 w-7 items-center justify-center rounded-full border-2 text-xs font-bold transition-all",
          isComplete && "border-emerald-500 bg-emerald-500 text-white",
          isActive && "border-primary bg-primary text-primary-foreground animate-pulse",
          !isComplete && !isActive && "border-muted-foreground/30 text-muted-foreground/50"
        )}
      >
        {isComplete ? (
          <CheckCircle2 className="h-4 w-4" />
        ) : isActive ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          thisIdx + 1
        )}
      </div>
      <span
        className={cn(
          "text-sm",
          isActive && "font-semibold",
          !isComplete && !isActive && "text-muted-foreground"
        )}
      >
        {label}
      </span>
    </div>
  );
}

export default function ProgressPage() {
  const router = useRouter();
  const { state } = usePipelineStatus();

  const status = state?.status ?? "idle";
  const progress = state?.progress;
  const config = state?.config;

  const jobPercent =
    progress?.total_jobs && progress.current_jobs
      ? Math.min(100, Math.round((progress.current_jobs / progress.total_jobs) * 100))
      : 0;

  const handleCancel = async () => {
    try {
      await stopPipeline();
    } catch {}
  };

  if (status === "idle" && !state?.start_time) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Progress</h1>
          <p className="text-muted-foreground">No pipeline run in progress</p>
        </div>
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Activity className="h-12 w-12 text-muted-foreground/30 mb-4" />
            <p className="text-muted-foreground mb-4">
              Start a pipeline run to see progress here
            </p>
            <Button onClick={() => router.push("/run")}>
              Configure & Run
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            Pipeline Progress
          </h1>
          <p className="text-muted-foreground">
            {status === "running"
              ? "Pipeline is running..."
              : status === "completed"
              ? "Pipeline completed successfully"
              : status === "failed"
              ? "Pipeline failed"
              : status === "cancelling"
              ? "Cancelling..."
              : "Pipeline status"}
          </p>
        </div>
        {(status === "running" || status === "cancelling") && (
          <Button variant="destructive" onClick={handleCancel} disabled={status === "cancelling"}>
            <Square className="mr-2 h-4 w-4" />
            {status === "cancelling" ? "Cancelling..." : "Cancel Run"}
          </Button>
        )}
      </div>

      {/* Config Summary */}
      {config && config.profile && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">Run Configuration</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              <Badge variant="outline">Profile: {config.profile}</Badge>
              <Badge variant="outline">Batch Size: {config.batch_size}</Badge>
              {config.cores && (
                <Badge variant="outline">Cores: {config.cores}</Badge>
              )}
              {config.dry_run && (
                <Badge variant="secondary">Dry Run</Badge>
              )}
              {progress && (
                <Badge variant="outline">
                  {progress.subjects_total} subjects
                </Badge>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Phase Progress */}
      {progress && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {status === "running" && (
                <Loader2 className="h-5 w-5 animate-spin text-primary" />
              )}
              {status === "completed" && (
                <CheckCircle2 className="h-5 w-5 text-emerald-500" />
              )}
              {status === "failed" && (
                <XCircle className="h-5 w-5 text-destructive" />
              )}
              Pipeline Phases
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2 flex-wrap">
              {PIPELINE_PHASES.map((phase, i) => (
                <div key={phase} className="flex items-center gap-2">
                  <PhaseStep
                    phase={phase}
                    currentPhase={progress.phase}
                    label={PHASE_LABELS[phase] ?? phase}
                  />
                  {i < PIPELINE_PHASES.length - 1 && (
                    <ArrowRight className="h-4 w-4 text-muted-foreground/30 mx-1" />
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Job Progress */}
      {progress && progress.phase === "batching" && status === "running" && (
        <Card>
          <CardHeader>
            <CardTitle>
              Batch {progress.batch_num} of {progress.total_batches}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Progress value={jobPercent} className="h-4" />

            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">
                {progress.current_jobs} / {progress.total_jobs ?? "?"} jobs
                completed
              </span>
              <span className="font-medium">{jobPercent}%</span>
            </div>

            {progress.current_rule && (
              <div className="flex items-center gap-3 rounded-lg bg-muted p-3">
                <Loader2 className="h-4 w-4 animate-spin text-primary" />
                <div>
                  <p className="text-sm font-medium">
                    {RULE_DISPLAY_NAMES[progress.current_rule] ??
                      progress.current_rule}
                  </p>
                  {progress.current_subject && (
                    <p className="text-xs text-muted-foreground">
                      Processing sub-{progress.current_subject}
                    </p>
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Batch Timeline */}
      {progress &&
        (progress.completed_batches.length > 0 ||
          progress.failed_batches.length > 0) && (
          <Card>
            <CardHeader>
              <CardTitle>Batch Timeline</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {Array.from(
                  { length: progress.total_batches },
                  (_, i) => i + 1
                ).map((batchNum) => {
                  const completed = progress.completed_batches.includes(batchNum);
                  const failed = progress.failed_batches.includes(batchNum);
                  const current =
                    batchNum === progress.batch_num && status === "running";

                  return (
                    <div
                      key={batchNum}
                      className={cn(
                        "flex items-center gap-3 rounded-lg border p-3",
                        completed && "border-emerald-500/30 bg-emerald-500/5",
                        failed && "border-destructive/30 bg-destructive/5",
                        current && "border-primary/50 bg-primary/5"
                      )}
                    >
                      {completed && (
                        <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                      )}
                      {failed && (
                        <XCircle className="h-5 w-5 text-destructive" />
                      )}
                      {current && (
                        <Loader2 className="h-5 w-5 animate-spin text-primary" />
                      )}
                      {!completed && !failed && !current && (
                        <div className="h-5 w-5 rounded-full border-2 border-muted-foreground/20" />
                      )}
                      <span className="text-sm font-medium">
                        Batch {batchNum}
                      </span>
                      {completed && (
                        <Badge className="ml-auto bg-emerald-500/10 text-emerald-600 border-emerald-500/20">
                          Complete
                        </Badge>
                      )}
                      {failed && (
                        <Badge variant="destructive" className="ml-auto">
                          Failed
                        </Badge>
                      )}
                      {current && (
                        <Badge variant="secondary" className="ml-auto">
                          Running
                        </Badge>
                      )}
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        )}

      {/* Error */}
      {state?.error && (
        <Card className="border-destructive/50">
          <CardHeader>
            <CardTitle className="text-destructive">Error</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm font-mono">{state.error}</p>
          </CardContent>
        </Card>
      )}

      {/* Completion Actions */}
      {(status === "completed" || status === "failed") && (
        <Card>
          <CardContent className="flex gap-3 pt-6">
            {status === "completed" && (
              <Button onClick={() => router.push("/results")}>
                <ArrowRight className="mr-2 h-4 w-4" />
                View Results
              </Button>
            )}
            <Button variant="outline" onClick={() => router.push("/logs")}>
              View Logs
            </Button>
            <Button variant="outline" onClick={() => router.push("/run")}>
              New Run
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Timing Info */}
      {state?.start_time && (
        <div className="text-xs text-muted-foreground">
          <Separator className="mb-3" />
          <p>Started: {new Date(state.start_time).toLocaleString()}</p>
          {state.end_time && (
            <p>Ended: {new Date(state.end_time).toLocaleString()}</p>
          )}
          {state.log_dir && <p>Log directory: {state.log_dir}</p>}
        </div>
      )}
    </div>
  );
}
