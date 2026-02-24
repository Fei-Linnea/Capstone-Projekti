"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Play, Plus, Trash2, Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
// Profile is fixed to tyks — Select component no longer needed
import { Switch } from "@/components/ui/switch";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  getProfile,
  getDefaults,
  discoverSubjects,
  startPipeline,
} from "@/lib/api";
import type { PipelineConfig, ProfileConfig } from "@/lib/types";
import { usePipelineStatus } from "@/lib/hooks";

const FIXED_PROFILE = "tyks";

export default function RunPipelinePage() {
  const router = useRouter();
  const { state } = usePipelineStatus();
  const isRunning = state?.status === "running" || state?.status === "cancelling";

  // Form state — profile is fixed to tyks
  const selectedProfile = FIXED_PROFILE;
  const [profileConfig, setProfileConfig] = useState<Record<string, unknown> | null>(null);
  const [batchSize, setBatchSize] = useState(5);
  const [cores, setCores] = useState<string>("");
  const [useAllCores, setUseAllCores] = useState(false);
  const [threadOverrides, setThreadOverrides] = useState<{ key: string; value: string }[]>([]);
  const [bidsPattern, setBidsPattern] = useState("");
  const [autoDiscover, setAutoDiscover] = useState(true);
  const [availableSubjects, setAvailableSubjects] = useState<string[]>([]);
  const [selectedSubjects, setSelectedSubjects] = useState<Set<string>>(new Set());
  const [dryRun, setDryRun] = useState(false);
  const [cleanup, setCleanup] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  // Load defaults and tyks profile on mount
  useEffect(() => {
    getDefaults()
      .then((d) => {
        setBatchSize(d.batch_size);
        setBidsPattern(d.bids_pattern);
      })
      .catch(() => {});
    getProfile(FIXED_PROFILE)
      .then((p) => {
        setProfileConfig(p.config);
        if (p.config.cores) {
          setCores(String(p.config.cores));
        }
      })
      .catch(() => {});
  }, []);

  // Discover subjects
  useEffect(() => {
    if (!autoDiscover) return;
    discoverSubjects(bidsPattern)
      .then((res) => setAvailableSubjects(res.subjects))
      .catch(() => setAvailableSubjects([]));
  }, [autoDiscover, bidsPattern]);

  const addThreadOverride = () => {
    setThreadOverrides([...threadOverrides, { key: "", value: "" }]);
  };

  const removeThreadOverride = (index: number) => {
    setThreadOverrides(threadOverrides.filter((_, i) => i !== index));
  };

  const updateThreadOverride = (index: number, field: "key" | "value", val: string) => {
    const updated = [...threadOverrides];
    updated[index][field] = val;
    setThreadOverrides(updated);
  };

  const toggleSubject = (subjectId: string) => {
    const next = new Set(selectedSubjects);
    if (next.has(subjectId)) {
      next.delete(subjectId);
    } else {
      next.add(subjectId);
    }
    setSelectedSubjects(next);
  };

  const selectAllSubjects = () => {
    setSelectedSubjects(new Set(availableSubjects));
  };

  const deselectAllSubjects = () => {
    setSelectedSubjects(new Set());
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    setError("");

    const config: Partial<PipelineConfig> = {
      profile: selectedProfile,
      batch_size: batchSize,
      cores: useAllCores ? "all" : cores ? Number(cores) : null,
      bids_pattern: bidsPattern,
      dry_run: dryRun,
      cleanup: cleanup,
    };

    // Thread overrides
    const threads = threadOverrides
      .filter((t) => t.key && t.value)
      .map((t) => `${t.key}=${t.value}`);
    if (threads.length > 0) {
      config.set_threads = threads;
    }

    // Subjects
    if (!autoDiscover && selectedSubjects.size > 0) {
      config.subjects = Array.from(selectedSubjects);
    }

    try {
      await startPipeline(config);
      router.push("/progress");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to start pipeline");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Run Pipeline</h1>
        <p className="text-muted-foreground">
          Configure and launch a hippocampus feature extraction run
        </p>
      </div>

      {isRunning && (
        <Card className="border-amber-500/50 bg-amber-500/5">
          <CardContent className="pt-6">
            <p className="text-sm text-amber-600">
              A pipeline run is already in progress. You cannot start a new run until it completes.
            </p>
            <Button
              variant="outline"
              className="mt-2"
              onClick={() => router.push("/progress")}
            >
              View Progress
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Profile (fixed to tyks) */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-3">Profile
            <Badge variant="secondary" className="text-sm font-mono">{FIXED_PROFILE}</Badge>
          </CardTitle>
          <CardDescription>
            Snakemake execution profile (fixed to TYKS)
          </CardDescription>
        </CardHeader>
        <CardContent>
          {profileConfig && (
            <div className="rounded-lg bg-muted p-3">
              <p className="text-xs font-medium text-muted-foreground mb-2">
                Profile Settings
              </p>
              <div className="grid grid-cols-2 gap-2 text-sm">
                {Object.entries(profileConfig).map(([key, value]) => (
                  <div key={key} className="flex justify-between">
                    <span className="text-muted-foreground">{key}:</span>
                    <span className="font-mono text-xs">{String(value)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Processing Options */}
      <Card>
        <CardHeader>
          <CardTitle>Processing Options</CardTitle>
          <CardDescription>
            Configure batch size, cores, and thread overrides
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="batch-size">Batch Size</Label>
              <Input
                id="batch-size"
                type="number"
                min={1}
                value={batchSize}
                onChange={(e) => setBatchSize(Number(e.target.value))}
              />
              <p className="text-xs text-muted-foreground">
                Number of subjects per batch
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="cores">Cores</Label>
              <div className="flex items-center gap-2">
                <Input
                  id="cores"
                  type="number"
                  min={1}
                  value={cores}
                  onChange={(e) => setCores(e.target.value)}
                  disabled={useAllCores}
                  className="flex-1"
                />
                <div className="flex items-center gap-1.5">
                  <Switch
                    checked={useAllCores}
                    onCheckedChange={setUseAllCores}
                  />
                  <Label className="text-xs">All</Label>
                </div>
              </div>
              <p className="text-xs text-muted-foreground">
                Override profile cores
              </p>
            </div>
          </div>

          <Separator />

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>Thread Overrides</Label>
              <Button variant="outline" size="sm" onClick={addThreadOverride}>
                <Plus className="mr-1 h-3 w-3" /> Add
              </Button>
            </div>
            {threadOverrides.map((t, i) => (
              <div key={i} className="flex items-center gap-2">
                <Input
                  placeholder="Rule name (e.g., hsf_segmentation)"
                  value={t.key}
                  onChange={(e) => updateThreadOverride(i, "key", e.target.value)}
                  className="flex-1"
                />
                <span className="text-muted-foreground">=</span>
                <Input
                  placeholder="Threads"
                  type="number"
                  min={1}
                  value={t.value}
                  onChange={(e) => updateThreadOverride(i, "value", e.target.value)}
                  className="w-24"
                />
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => removeThreadOverride(i)}
                >
                  <Trash2 className="h-4 w-4 text-muted-foreground" />
                </Button>
              </div>
            ))}
            {threadOverrides.length === 0 && (
              <p className="text-xs text-muted-foreground">
                No thread overrides configured
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Subject Selection */}
      <Card>
        <CardHeader>
          <CardTitle>Subjects</CardTitle>
          <CardDescription>
            Choose which subjects to process
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="bids-pattern">BIDS Pattern</Label>
            <Input
              id="bids-pattern"
              value={bidsPattern}
              onChange={(e) => setBidsPattern(e.target.value)}
              placeholder="sub-*/ses-*/anat/*_T1w.nii.gz"
              className="font-mono text-sm"
            />
          </div>

          <div className="flex items-center gap-2">
            <Switch checked={autoDiscover} onCheckedChange={setAutoDiscover} />
            <Label>Auto-discover all subjects</Label>
          </div>

          {!autoDiscover && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label>
                  Select Subjects ({selectedSubjects.size} / {availableSubjects.length})
                </Label>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" onClick={selectAllSubjects}>
                    Select All
                  </Button>
                  <Button variant="outline" size="sm" onClick={deselectAllSubjects}>
                    Deselect All
                  </Button>
                </div>
              </div>
              <div className="grid grid-cols-4 gap-2 max-h-48 overflow-y-auto rounded-lg border p-3">
                {availableSubjects.length === 0 ? (
                  <p className="col-span-4 text-sm text-muted-foreground">
                    No subjects found at /data
                  </p>
                ) : (
                  availableSubjects.map((s) => (
                    <label
                      key={s}
                      className="flex items-center gap-2 text-sm cursor-pointer"
                    >
                      <Checkbox
                        checked={selectedSubjects.has(s)}
                        onCheckedChange={() => toggleSubject(s)}
                      />
                      sub-{s}
                    </label>
                  ))
                )}
              </div>
            </div>
          )}

          {autoDiscover && availableSubjects.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {availableSubjects.slice(0, 20).map((s) => (
                <Badge key={s} variant="secondary" className="text-xs">
                  sub-{s}
                </Badge>
              ))}
              {availableSubjects.length > 20 && (
                <Badge variant="outline" className="text-xs">
                  +{availableSubjects.length - 20} more
                </Badge>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Execution Control */}
      <Card>
        <CardHeader>
          <CardTitle>Execution</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Switch checked={dryRun} onCheckedChange={setDryRun} />
              <Label>Dry Run</Label>
            </div>
            <div className="flex items-center gap-2">
              <Switch checked={cleanup} onCheckedChange={setCleanup} />
              <Label>Cleanup after completion</Label>
            </div>
          </div>

          {error && (
            <p className="text-sm text-destructive">{error}</p>
          )}

          <Button
            size="lg"
            className="w-full"
            onClick={handleSubmit}
            disabled={submitting || isRunning}
          >
            {submitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Starting...
              </>
            ) : (
              <>
                <Play className="mr-2 h-4 w-4" />
                {dryRun ? "Start Dry Run" : "Start Pipeline"}
              </>
            )}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
