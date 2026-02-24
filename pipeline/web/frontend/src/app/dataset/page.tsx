"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  FolderOpen,
  File,
  ChevronRight,
  ArrowUp,
  ArrowLeft,
  HardDrive,
  Users,
  FileStack,
  RefreshCw,
  Brain,
  Image,
  FileText,
  Archive,
  CheckCircle2,
  FolderSearch,
  ArrowRight,
  Database,
  Monitor,
  Search,
  CornerDownLeft,
  Pencil,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  getCurrentDataset,
  getDrives,
  browseDataset,
  selectDataset,
  selectDatasetByPath,
} from "@/lib/api";
import type {
  DatasetCurrentResponse,
  DatasetEntry,
  DatasetBrowseResponse,
  DriveInfo,
} from "@/lib/types";
import { cn } from "@/lib/utils";

/* ── Icon helper ──────────────────────────────────────────────────── */

function EntryIcon({ entry }: { entry: DatasetEntry }) {
  if (entry.type === "directory") {
    if (entry.name.startsWith("sub-"))
      return <Brain className="h-4 w-4 text-violet-500 shrink-0" />;
    if (entry.name.startsWith("ses-"))
      return <FolderOpen className="h-4 w-4 text-amber-500 shrink-0" />;
    if (["anat", "func", "dwi", "fmap"].includes(entry.name))
      return <FolderOpen className="h-4 w-4 text-emerald-500 shrink-0" />;
    if (entry.name === "derivatives")
      return <FolderOpen className="h-4 w-4 text-orange-500 shrink-0" />;
    if (entry.has_subjects)
      return <Database className="h-4 w-4 text-violet-600 shrink-0" />;
    return <FolderOpen className="h-4 w-4 text-sky-500 shrink-0" />;
  }
  const ext = entry.extension?.toLowerCase() ?? "";
  if (ext === ".nii" || ext === ".gz")
    return <Image className="h-4 w-4 text-emerald-500 shrink-0" />;
  if (ext === ".json")
    return <FileText className="h-4 w-4 text-amber-500 shrink-0" />;
  if (ext === ".tsv" || ext === ".csv")
    return <FileStack className="h-4 w-4 text-blue-500 shrink-0" />;
  if (ext === ".tar" || ext === ".zip")
    return <Archive className="h-4 w-4 text-gray-500 shrink-0" />;
  return <File className="h-4 w-4 text-muted-foreground shrink-0" />;
}

/* ── helpers ──────────────────────────────────────────────────────── */

/** Detect whether a drive entry looks like a Windows drive letter (single char) */
function isWindowsDrive(driveName: string): boolean {
  return driveName.length === 1 && /^[a-zA-Z]$/.test(driveName);
}

/**
 * Convert container path to a human-readable display string.
 *  - Windows drive "d"  + path "d/Work/Data"  → "D:\Work\Data"
 *  - Linux root  "root" + path "root/home/user" → "/home/user"
 *  - Other mount  "data" + path "data/sets"      → "/data/sets"
 */
function toDisplayPath(containerPath: string, drive: string): string {
  const parts = containerPath ? containerPath.split("/").filter(Boolean) : [];
  const rest = parts.length > 0 && parts[0] === drive ? parts.slice(1) : parts;

  if (isWindowsDrive(drive)) {
    return rest.length > 0
      ? `${drive.toUpperCase()}:\\${rest.join("\\")}`
      : `${drive.toUpperCase()}:\\`;
  }
  if (drive === "root") {
    return rest.length > 0 ? `/${rest.join("/")}` : "/";
  }
  return rest.length > 0 ? `/${drive}/${rest.join("/")}` : `/${drive}`;
}

/** Display prefix for the breadcrumb address bar */
function drivePrefix(drive: string): string {
  if (isWindowsDrive(drive)) return `${drive.toUpperCase()}:\\`;
  if (drive === "root") return "/";
  return `/${drive}/`;
}

/* ── Main Page ────────────────────────────────────────────────────── */

export default function DatasetPage() {
  const router = useRouter();
  const [current, setCurrent] = useState<DatasetCurrentResponse | null>(null);
  const [drives, setDrives] = useState<DriveInfo[]>([]);
  const [activeDrive, setActiveDrive] = useState("");
  const [browse, setBrowse] = useState<DatasetBrowseResponse | null>(null);
  const [currentPath, setCurrentPath] = useState("");
  const [loading, setLoading] = useState(true);
  const [selecting, setSelecting] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");
  const [error, setError] = useState("");

  // Editable address bar
  const [addressEditing, setAddressEditing] = useState(false);
  const [addressText, setAddressText] = useState("");
  const addressInputRef = useRef<HTMLInputElement>(null);

  // Manual path input (bottom card)
  const [manualPath, setManualPath] = useState("");
  const [manualError, setManualError] = useState("");
  const [manualLoading, setManualLoading] = useState(false);

  const loadCurrent = useCallback(() => {
    getCurrentDataset()
      .then(setCurrent)
      .catch(() => setCurrent(null));
  }, []);

  const navigateTo = useCallback((path: string) => {
    setCurrentPath(path);
    setLoading(true);
    setError("");
    setSuccessMsg("");
    browseDataset(path, "host")
      .then((data) => {
        setBrowse(data);
        setLoading(false);
      })
      .catch((e) => {
        setError(e instanceof Error ? e.message : "Failed to browse");
        setLoading(false);
      });
  }, []);

  // Load drives and initial data
  useEffect(() => {
    loadCurrent();
    getDrives()
      .then((data) => {
        setDrives(data.drives);
        const firstAccessible = data.drives.find((d) => d.accessible);
        if (firstAccessible) {
          setActiveDrive(firstAccessible.name);
          navigateTo(firstAccessible.name);
        } else {
          navigateTo("");
        }
      })
      .catch(() => navigateTo(""));
  }, [loadCurrent, navigateTo]);

  const handleDriveSelect = (driveName: string) => {
    setActiveDrive(driveName);
    navigateTo(driveName);
  };

  const handleSelect = async (path: string) => {
    setSelecting(true);
    setError("");
    setSuccessMsg("");
    try {
      const res = await selectDataset(path);
      setSuccessMsg(
        `Dataset selected! Found ${res.subject_count} subject${res.subject_count !== 1 ? "s" : ""}.`
      );
      loadCurrent();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to select dataset");
    } finally {
      setSelecting(false);
    }
  };

  const handleManualSelect = async () => {
    const path = manualPath.trim();
    if (!path) {
      setManualError("Please enter a path");
      return;
    }
    setManualLoading(true);
    setManualError("");
    setSuccessMsg("");
    try {
      const res = await selectDatasetByPath(path);
      setSuccessMsg(
        `Dataset selected! Found ${res.subject_count} subject${res.subject_count !== 1 ? "s" : ""}.`
      );
      setManualPath("");
      loadCurrent();
    } catch (e) {
      setManualError(
        e instanceof Error ? e.message : "Failed to select dataset"
      );
    } finally {
      setManualLoading(false);
    }
  };

  /** Navigate from the editable address bar — accepts Windows (D:\foo) or Unix-style paths */
  const handleAddressBarGo = () => {
    const raw = addressText.trim();
    if (!raw) {
      setAddressEditing(false);
      return;
    }
    setAddressEditing(false);

    // Detect Windows-style path like D:\foo\bar or D:/foo/bar
    const winMatch = raw.match(/^([A-Za-z]):[\\\/]?(.*)?$/);
    if (winMatch) {
      const drive = winMatch[1].toLowerCase();
      const rest = (winMatch[2] ?? "").replace(/\\/g, "/").replace(/\/+$/, "");
      const newPath = rest ? `${drive}/${rest}` : drive;
      // Switch active drive if needed
      if (drive !== activeDrive) setActiveDrive(drive);
      navigateTo(newPath);
      return;
    }
    // Otherwise treat as relative / container path
    navigateTo(raw.replace(/\\/g, "/"));
  };

  const startAddressEdit = () => {
    setAddressText(toDisplayPath(currentPath, activeDrive));
    setAddressEditing(true);
    setTimeout(() => addressInputRef.current?.select(), 0);
  };

  const goUp = () => {
    if (!currentPath || currentPath === activeDrive) return;
    const parent = browse?.parent ?? activeDrive;
    navigateTo(parent);
  };

  const dirs = browse?.entries.filter((e) => e.type === "directory") ?? [];
  const files = browse?.entries.filter((e) => e.type === "file") ?? [];

  /* ── breadcrumb segments ──────────────────────────────────────── */
  const pathParts = currentPath ? currentPath.split("/").filter(Boolean) : [];
  const displayParts =
    pathParts.length > 0 && pathParts[0] === activeDrive
      ? pathParts.slice(1)
      : pathParts;

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Select Dataset</h1>
        <p className="text-muted-foreground">
          Browse your drives or paste a path to select a BIDS dataset
        </p>
      </div>

      {/* ── Current Dataset Status ─────────────────────────────────── */}
      {current && (
        <Card
          className={cn(
            current.selected_path
              ? "border-emerald-500/50 bg-emerald-500/5"
              : "border-amber-500/50 bg-amber-500/5"
          )}
        >
          <CardContent className="pt-6">
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-start gap-3">
                {current.selected_path ? (
                  <CheckCircle2 className="h-6 w-6 text-emerald-500 mt-0.5" />
                ) : (
                  <FolderSearch className="h-6 w-6 text-amber-500 mt-0.5" />
                )}
                <div>
                  <p className="font-semibold">
                    {current.selected_path
                      ? "Dataset Selected"
                      : "No Dataset Selected"}
                  </p>
                  {current.selected_path ? (
                    <div className="mt-1 space-y-1">
                      <p className="text-sm text-muted-foreground font-mono">
                        {current.data_dir}
                      </p>
                      <div className="flex gap-4 text-sm">
                        <span className="flex items-center gap-1">
                          <Users className="h-3.5 w-3.5" />{" "}
                          {current.subject_count} subjects
                        </span>
                        <span className="flex items-center gap-1">
                          <FileStack className="h-3.5 w-3.5" />{" "}
                          {current.total_files.toLocaleString()} files
                        </span>
                        <span className="flex items-center gap-1">
                          <HardDrive className="h-3.5 w-3.5" />{" "}
                          {current.total_size_human}
                        </span>
                      </div>
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground mt-1">
                      Browse below or paste a path to select your BIDS dataset
                    </p>
                  )}
                </div>
              </div>
              {current.selected_path && (
                <Button size="sm" onClick={() => router.push("/run")}>
                  <ArrowRight className="mr-2 h-4 w-4" />
                  Run Pipeline
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* ── Success message ────────────────────────────────────────── */}
      {successMsg && (
        <Card className="border-emerald-500/50 bg-emerald-500/5">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                <p className="text-sm font-medium text-emerald-700">
                  {successMsg}
                </p>
              </div>
              <div className="flex gap-2">
                <Button size="sm" onClick={() => router.push("/run")}>
                  <ArrowRight className="mr-2 h-4 w-4" />
                  Run Pipeline
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => router.push("/")}
                >
                  Dashboard
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* ── File Browser ──────────────────────────────────────────── */}
      <Card>
        {/* ── Drive Tabs ─────────────────────────────────────────── */}
        <div className="flex items-center gap-1 px-4 pt-4 pb-2">
          {drives.map((drive) => (
            <Button
              key={drive.name}
              variant={drive.name === activeDrive ? "default" : "outline"}
              size="sm"
              className={cn(
                "gap-1.5",
                drive.name === activeDrive &&
                  "bg-primary text-primary-foreground shadow"
              )}
              onClick={() => handleDriveSelect(drive.name)}
              disabled={!drive.accessible}
            >
              <HardDrive className="h-3.5 w-3.5" />
              {drive.label}
            </Button>
          ))}

          <div className="ml-auto flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={goUp}
              disabled={!currentPath || currentPath === activeDrive}
              title="Go up one level"
            >
              <ArrowUp className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => navigateTo(currentPath)}
              className="h-8 w-8"
              title="Refresh"
            >
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* ── Address Bar (clickable breadcrumbs / editable input) ── */}
        <div className="px-4 pb-3">
          {addressEditing ? (
            <div className="flex items-center gap-2">
              <Input
                ref={addressInputRef}
                autoFocus
                value={addressText}
                onChange={(e) => setAddressText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleAddressBarGo();
                  if (e.key === "Escape") setAddressEditing(false);
                }}
                onBlur={() => setAddressEditing(false)}
                placeholder={isWindowsDrive(activeDrive) ? "D:\\Work\\Data\\MyDataset" : "/home/user/data/dataset"}
                className="font-mono text-sm h-9"
              />
              <Button
                size="sm"
                variant="secondary"
                className="shrink-0 h-9 px-3"
                onMouseDown={(e) => {
                  e.preventDefault(); // prevent blur
                  handleAddressBarGo();
                }}
              >
                <CornerDownLeft className="h-4 w-4 mr-1" />
                Go
              </Button>
            </div>
          ) : (
            <button
              onClick={startAddressEdit}
              className="flex items-center w-full gap-1 text-sm rounded-md border bg-muted/40 px-3 py-2 hover:bg-muted transition-colors cursor-text group"
              title="Click to type a path"
            >
              <Monitor className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
              <span className="font-medium">{drivePrefix(activeDrive)}</span>
              {displayParts.map((part, i) => {
                const segPath = [activeDrive, ...displayParts.slice(0, i + 1)].join("/");
                const isLast = i === displayParts.length - 1;
                return (
                  <span key={segPath} className="flex items-center gap-1">
                    <ChevronRight className="h-3 w-3 text-muted-foreground/50" />
                    <span
                      onClick={(e) => {
                        e.stopPropagation();
                        navigateTo(segPath);
                      }}
                      className={cn(
                        "hover:underline cursor-pointer rounded px-0.5",
                        isLast
                          ? "font-semibold text-foreground"
                          : "text-muted-foreground"
                      )}
                    >
                      {part}
                    </span>
                  </span>
                );
              })}
              <Pencil className="h-3 w-3 text-muted-foreground/30 group-hover:text-muted-foreground ml-auto shrink-0 transition-colors" />
            </button>
          )}
        </div>

        {/* ── BIDS detect + item count bar ──────────────────────── */}
        <div className="flex items-center justify-between px-4 pb-2">
          <div className="flex items-center gap-2">
            {browse?.is_bids && (
              <Button
                size="sm"
                className="bg-emerald-600 hover:bg-emerald-700"
                onClick={() => handleSelect(currentPath)}
                disabled={selecting}
              >
                <CheckCircle2 className="mr-2 h-4 w-4" />
                {selecting ? "Selecting..." : "Use This Directory as Dataset"}
              </Button>
            )}
          </div>
          {browse && (
            <span className="text-xs text-muted-foreground whitespace-nowrap">
              {browse.total} items
            </span>
          )}
        </div>

        <Separator />
        <CardContent className="p-0">
          {/* Error */}
          {error && (
            <div className="p-6 text-center">
              <p className="text-sm text-destructive">{error}</p>
              <Button
                variant="outline"
                size="sm"
                className="mt-2"
                onClick={() =>
                  activeDrive ? navigateTo(activeDrive) : navigateTo("")
                }
              >
                Go to drive root
              </Button>
            </div>
          )}

          {/* Loading */}
          {loading && !error && (
            <div className="flex items-center justify-center py-12">
              <RefreshCw className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          )}

          {/* Empty */}
          {!loading && !error && browse && browse.entries.length === 0 && (
            <div className="flex flex-col items-center justify-center py-12">
              <FolderOpen className="h-12 w-12 text-muted-foreground/20 mb-3" />
              <p className="text-muted-foreground text-sm">
                This directory is empty
              </p>
            </div>
          )}

          {/* Directory listing */}
          {!loading && !error && browse && browse.entries.length > 0 && (
            <ScrollArea className="h-125">
              {/* Back / parent button */}
              {currentPath && currentPath !== activeDrive && (
                <button
                  onClick={goUp}
                  className="flex w-full items-center gap-3 border-b px-4 py-2.5 text-sm text-muted-foreground hover:bg-accent transition-colors"
                >
                  <ArrowLeft className="h-4 w-4" />
                  <span>.. (up one level)</span>
                </button>
              )}

              {/* Directories */}
              {dirs.map((entry) => (
                <div
                  key={entry.path}
                  className="flex w-full items-center border-b hover:bg-accent/50 transition-colors group"
                >
                  <button
                    onClick={() => navigateTo(entry.path)}
                    className="flex flex-1 items-center gap-3 px-4 py-2.5 text-sm min-w-0"
                  >
                    <EntryIcon entry={entry} />
                    <span className="flex-1 text-left font-medium group-hover:text-primary transition-colors truncate">
                      {entry.name}
                    </span>
                    {entry.has_subjects && (
                      <Badge className="bg-violet-500/10 text-violet-600 border-violet-500/20 text-[10px] shrink-0">
                        BIDS
                      </Badge>
                    )}
                    {entry.child_count !== undefined && (
                      <span className="text-xs text-muted-foreground shrink-0">
                        {entry.child_count} items
                      </span>
                    )}
                    <ChevronRight className="h-4 w-4 text-muted-foreground/40 group-hover:text-primary transition-colors shrink-0" />
                  </button>
                  {entry.has_subjects && (
                    <Button
                      size="sm"
                      variant="ghost"
                      className="mr-2 text-xs text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50 shrink-0"
                      onClick={() => handleSelect(entry.path)}
                      disabled={selecting}
                    >
                      Select
                    </Button>
                  )}
                </div>
              ))}

              {/* Files */}
              {files.map((entry) => (
                <div
                  key={entry.path}
                  className="flex w-full items-center gap-3 border-b px-4 py-2.5 text-sm"
                >
                  <EntryIcon entry={entry} />
                  <span className="flex-1 text-left truncate text-muted-foreground">
                    {entry.name}
                  </span>
                  {entry.extension && (
                    <Badge
                      variant="outline"
                      className="text-[10px] px-1.5 py-0 font-mono"
                    >
                      {entry.extension}
                    </Badge>
                  )}
                  {entry.size_human && (
                    <span className="text-xs text-muted-foreground whitespace-nowrap">
                      {entry.size_human}
                    </span>
                  )}
                </div>
              ))}
            </ScrollArea>
          )}
        </CardContent>
      </Card>

      {/* ── Quick Path Input (bottom) ─────────────────────────────── */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-sm">
            <Search className="h-4 w-4" />
            Enter Path Directly
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Input
              value={manualPath}
              onChange={(e) => {
                setManualPath(e.target.value);
                setManualError("");
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleManualSelect();
              }}
              placeholder="D:\Data\MyBidsDataset  or  /home/user/datasets/study1"
              className="font-mono text-sm"
            />
            <Button
              onClick={handleManualSelect}
              disabled={manualLoading || !manualPath.trim()}
              className="shrink-0"
            >
              {manualLoading ? (
                <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <FolderOpen className="mr-2 h-4 w-4" />
              )}
              Select
            </Button>
          </div>
          {manualError && (
            <p className="text-sm text-destructive mt-2">{manualError}</p>
          )}
          <p className="text-xs text-muted-foreground mt-2">
            Paste the full path to your BIDS dataset directory (e.g.{" "}
            <code className="bg-muted px-1 py-0.5 rounded">
              D:\Data\MyStudy
            </code>{" "}
            or{" "}
            <code className="bg-muted px-1 py-0.5 rounded">
              /home/user/datasets/study1
            </code>
            )
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
