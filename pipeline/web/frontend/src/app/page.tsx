"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Activity,
  Play,
  Table2,
  FileText,
  Users,
  Clock,
  CheckCircle2,
  XCircle,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { StatusDot } from "@/components/status-dot";
import { usePipelineStatus } from "@/lib/hooks";
import { discoverSubjects } from "@/lib/api";
import { PHASE_LABELS } from "@/lib/types";

export default function DashboardPage() {
  const { state } = usePipelineStatus();
  const [subjectCount, setSubjectCount] = useState<number | null>(null);

  useEffect(() => {
    discoverSubjects()
      .then((res) => setSubjectCount(res.count))
      .catch(() => setSubjectCount(null));
  }, []);

  const status = state?.status ?? "idle";
  const progress = state?.progress;

  const jobPercent =
    progress?.total_jobs && progress.current_jobs
      ? Math.round((progress.current_jobs / progress.total_jobs) * 100)
      : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Hippocampus Radiomic Feature Extraction Pipeline
        </p>
      </div>

      {/* Status Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {/* Pipeline Status */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">
              Pipeline Status
            </CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <StatusDot status={status} />
              <span className="text-2xl font-bold capitalize">{status}</span>
            </div>
            {progress && status === "running" && (
              <p className="text-xs text-muted-foreground mt-1">
                {PHASE_LABELS[progress.phase] ?? progress.phase}
              </p>
            )}
          </CardContent>
        </Card>

        {/* Subjects */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">
              Subjects at /data
            </CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {subjectCount !== null ? subjectCount : "\u2014"}
            </div>
            <p className="text-xs text-muted-foreground">
              auto-discovered via BIDS pattern
            </p>
          </CardContent>
        </Card>

        {/* Last Run */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Last Run</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {state?.start_time
                ? new Date(state.start_time).toLocaleDateString()
                : "\u2014"}
            </div>
            {state?.start_time && (
              <p className="text-xs text-muted-foreground">
                {new Date(state.start_time).toLocaleTimeString()}
              </p>
            )}
          </CardContent>
        </Card>

        {/* Result */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Result</CardTitle>
            {status === "completed" ? (
              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
            ) : status === "failed" ? (
              <XCircle className="h-4 w-4 text-destructive" />
            ) : (
              <Activity className="h-4 w-4 text-muted-foreground" />
            )}
          </CardHeader>
          <CardContent>
            {status === "completed" ? (
              <Badge className="bg-emerald-500/10 text-emerald-600 border-emerald-500/20">
                Success
              </Badge>
            ) : status === "failed" ? (
              <Badge variant="destructive">Failed</Badge>
            ) : status === "running" ? (
              <Badge variant="secondary">In Progress</Badge>
            ) : (
              <span className="text-sm text-muted-foreground">No runs yet</span>
            )}
            {state?.error && (
              <p className="text-xs text-destructive mt-1 truncate">
                {state.error}
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Live Progress (when running) */}
      {status === "running" && progress && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5 animate-pulse text-emerald-500" />
              Live Progress
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between text-sm">
              <span>
                Batch {progress.batch_num} of {progress.total_batches}
              </span>
              <span className="text-muted-foreground">
                {progress.subjects_total} subjects total
              </span>
            </div>

            <Progress value={jobPercent} className="h-3" />

            <div className="flex items-center justify-between text-sm text-muted-foreground">
              <span>
                {progress.current_jobs} / {progress.total_jobs ?? "?"} jobs
              </span>
              <span>{jobPercent}%</span>
            </div>

            {progress.current_rule && (
              <div className="flex items-center gap-2 text-sm">
                <Badge variant="outline">{progress.current_rule}</Badge>
                {progress.current_subject && (
                  <span className="text-muted-foreground">
                    sub-{progress.current_subject}
                  </span>
                )}
              </div>
            )}

            <Separator />

            <div className="flex gap-2 flex-wrap">
              {progress.completed_batches.map((b) => (
                <Badge
                  key={b}
                  className="bg-emerald-500/10 text-emerald-600 border-emerald-500/20"
                >
                  Batch {b} <CheckCircle2 className="ml-1 h-3 w-3" />
                </Badge>
              ))}
              {progress.failed_batches.map((b) => (
                <Badge key={String(b)} variant="destructive">
                  {typeof b === "number" ? `Batch ${b}` : b}{" "}
                  <XCircle className="ml-1 h-3 w-3" />
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-3">
          <Link href="/run">
            <Button>
              <Play className="mr-2 h-4 w-4" />
              New Run
            </Button>
          </Link>
          <Link href="/results">
            <Button variant="outline">
              <Table2 className="mr-2 h-4 w-4" />
              View Results
            </Button>
          </Link>
          <Link href="/logs">
            <Button variant="outline">
              <FileText className="mr-2 h-4 w-4" />
              View Logs
            </Button>
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}
