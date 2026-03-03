"use client";

import { useEffect, useState } from "react";
import {
  FileText,
  ChevronRight,
  Download,
  FileCode,
  Folder,
  Clock,
  Eye,
  ChevronDown,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  getLogRuns,
  getLogFiles,
  getLogFileContent,
  getRulegraphUrl,
} from "@/lib/api";
import type { LogRun, LogFile, LogFileContent } from "@/lib/types";
import { cn } from "@/lib/utils";

export default function LogsPage() {
  const [runs, setRuns] = useState<LogRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<LogRun | null>(null);
  const [files, setFiles] = useState<LogFile[]>([]);
  const [selectedFile, setSelectedFile] = useState<LogFile | null>(null);
  const [fileContent, setFileContent] = useState<LogFileContent | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingFiles, setLoadingFiles] = useState(false);
  const [loadingContent, setLoadingContent] = useState(false);
  const [error, setError] = useState("");
  const [tailLines, setTailLines] = useState<number | undefined>(500);

  // Load runs on mount
  useEffect(() => {
    setLoading(true);
    getLogRuns()
      .then((data) => {
        setRuns(data);
        // Auto-select the most recent run
        if (data.length > 0) {
          setSelectedRun(data[0]);
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  // Load files when run is selected
  useEffect(() => {
    if (!selectedRun) {
      setFiles([]);
      setSelectedFile(null);
      setFileContent(null);
      return;
    }

    setLoadingFiles(true);
    getLogFiles(selectedRun.id)
      .then(setFiles)
      .catch((err) => setError(err.message))
      .finally(() => setLoadingFiles(false));
  }, [selectedRun]);

  // Load file content when file is selected
  const loadFileContent = (file: LogFile) => {
    if (!selectedRun) return;

    setSelectedFile(file);
    setLoadingContent(true);
    getLogFileContent(selectedRun.id, file.path, tailLines)
      .then(setFileContent)
      .catch((err) => setError(err.message))
      .finally(() => setLoadingContent(false));
  };

  // Group files by directory
  const groupedFiles = files.reduce((acc, file) => {
    const dir = file.path.includes("/")
      ? file.path.substring(0, file.path.lastIndexOf("/"))
      : "root";
    if (!acc[dir]) acc[dir] = [];
    acc[dir].push(file);
    return acc;
  }, {} as Record<string, LogFile[]>);

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold tracking-tight">Run Logs</h1>
        <Card>
          <CardContent className="flex items-center justify-center py-16">
            <p className="text-muted-foreground">Loading logs...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (runs.length === 0) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold tracking-tight">Run Logs</h1>
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <FileText className="h-12 w-12 text-muted-foreground/30 mb-4" />
            <p className="text-muted-foreground">No pipeline runs found</p>
            <p className="text-sm text-muted-foreground mt-2">
              Start a pipeline run to see logs here
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Run Logs</h1>
        <p className="text-muted-foreground">
          View logs and outputs from pipeline runs
        </p>
      </div>

      {error && (
        <Card className="border-destructive/50 bg-destructive/5">
          <CardContent className="pt-6">
            <p className="text-sm text-destructive">{error}</p>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Run List */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Clock className="h-4 w-4" />
              Pipeline Runs
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1">
            {runs.map((run) => (
              <button
                key={run.id}
                onClick={() => setSelectedRun(run)}
                className={cn(
                  "w-full text-left px-3 py-2 rounded-md text-sm transition-colors",
                  "hover:bg-accent",
                  selectedRun?.id === run.id && "bg-accent font-medium"
                )}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs">{run.id}</span>
                  <Badge variant="secondary" className="text-[10px] px-1.5">
                    {run.file_count}
                  </Badge>
                </div>
              </button>
            ))}
          </CardContent>
        </Card>

        {/* File List */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Folder className="h-4 w-4" />
              Log Files
              {selectedRun && (
                <span className="text-xs font-normal text-muted-foreground">
                  ({files.length} files)
                </span>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loadingFiles ? (
              <p className="text-sm text-muted-foreground">Loading files...</p>
            ) : files.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No log files found
              </p>
            ) : (
              <div className="space-y-4">
                {/* Rulegraph link if available */}
                {selectedRun && (
                  <div className="pb-2">
                    <a
                      href={getRulegraphUrl(selectedRun.id)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-primary hover:underline flex items-center gap-1"
                    >
                      <FileCode className="h-3 w-3" />
                      View Snakemake Rulegraph (SVG)
                    </a>
                  </div>
                )}

                {Object.entries(groupedFiles).map(([dir, dirFiles]) => (
                  <div key={dir}>
                    <h3 className="text-xs font-semibold text-muted-foreground mb-2 uppercase">
                      {dir === "root" ? "Root" : dir}
                    </h3>
                    <div className="space-y-1">
                      {dirFiles.map((file) => (
                        <button
                          key={file.path}
                          onClick={() => loadFileContent(file)}
                          className={cn(
                            "w-full text-left px-3 py-2 rounded-md text-sm transition-colors",
                            "hover:bg-accent flex items-center justify-between",
                            selectedFile?.path === file.path &&
                              "bg-accent font-medium"
                          )}
                        >
                          <div className="flex items-center gap-2 flex-1 min-w-0">
                            <FileText className="h-3.5 w-3.5 flex-shrink-0" />
                            <span className="truncate">{file.name}</span>
                          </div>
                          <span className="text-xs text-muted-foreground flex-shrink-0 ml-2">
                            {file.size_human}
                          </span>
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* File Content Viewer */}
      {selectedFile && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base flex items-center gap-2">
                <FileCode className="h-4 w-4" />
                {selectedFile.name}
                {fileContent && fileContent.truncated && (
                  <Badge variant="secondary" className="text-[10px] px-1.5">
                    Last {fileContent.lines_shown} lines
                  </Badge>
                )}
              </CardTitle>
              <div className="flex items-center gap-2">
                <select
                  value={tailLines ?? "all"}
                  onChange={(e) => {
                    const val = e.target.value;
                    const newTail = val === "all" ? undefined : parseInt(val);
                    setTailLines(newTail);
                    if (selectedFile && selectedRun) {
                      setLoadingContent(true);
                      getLogFileContent(selectedRun.id, selectedFile.path, newTail)
                        .then(setFileContent)
                        .catch((err) => setError(err.message))
                        .finally(() => setLoadingContent(false));
                    }
                  }}
                  className="text-xs border rounded px-2 py-1"
                >
                  <option value="100">Last 100 lines</option>
                  <option value="500">Last 500 lines</option>
                  <option value="1000">Last 1000 lines</option>
                  <option value="all">All lines</option>
                </select>
              </div>
            </div>
            {fileContent && (
              <p className="text-xs text-muted-foreground">
                {fileContent.total_lines.toLocaleString()} total lines
                {fileContent.truncated &&
                  ` (showing last ${fileContent.lines_shown})`}
              </p>
            )}
          </CardHeader>
          <CardContent>
            {loadingContent ? (
              <p className="text-sm text-muted-foreground">Loading content...</p>
            ) : fileContent ? (
              <pre className="text-xs bg-muted p-4 rounded-md overflow-x-auto max-h-[600px] overflow-y-auto font-mono">
                {fileContent.content}
              </pre>
            ) : (
              <p className="text-sm text-muted-foreground">
                Click a file to view its contents
              </p>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
