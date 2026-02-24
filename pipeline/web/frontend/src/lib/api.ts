/* ── API client functions for Flask backend ── */

import type {
  PipelineDefaults,
  ProfileConfig,
  SubjectsResponse,
  RunState,
  PipelineConfig,
  FeaturesResponse,
  LogRun,
  LogFile,
  LogFileContent,
  DatasetCurrentResponse,
  DatasetBrowseResponse,
  DatasetSelectResponse,
  DrivesResponse,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

async function fetchJSON<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, init);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error || `API error ${res.status}`);
  }
  return res.json();
}

/* ── Config ── */

export async function getProfiles(): Promise<string[]> {
  const data = await fetchJSON<{ profiles: string[] }>("/api/config/profiles");
  return data.profiles;
}

export async function getProfile(name: string): Promise<ProfileConfig> {
  return fetchJSON<ProfileConfig>(`/api/config/profiles/${name}`);
}

export async function getDefaults(): Promise<PipelineDefaults> {
  return fetchJSON<PipelineDefaults>("/api/config/defaults");
}

/* ── Subjects ── */

export async function discoverSubjects(bidsPattern?: string): Promise<SubjectsResponse> {
  const params = bidsPattern ? `?bids_pattern=${encodeURIComponent(bidsPattern)}` : "";
  return fetchJSON<SubjectsResponse>(`/api/subjects${params}`);
}

/* ── Pipeline ── */

export async function getStatus(): Promise<RunState> {
  return fetchJSON<RunState>("/api/pipeline/status");
}

export async function startPipeline(config: Partial<PipelineConfig>): Promise<{ message: string; log_dir: string }> {
  return fetchJSON("/api/pipeline/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
  });
}

export async function stopPipeline(): Promise<{ message: string }> {
  return fetchJSON("/api/pipeline/stop", { method: "POST" });
}

/* ── Results ── */

export async function getFeatures(params?: {
  page?: number;
  per_page?: number;
  sort?: string;
  order?: "asc" | "desc";
  search?: string;
}): Promise<FeaturesResponse> {
  const searchParams = new URLSearchParams();
  if (params?.page) searchParams.set("page", String(params.page));
  if (params?.per_page) searchParams.set("per_page", String(params.per_page));
  if (params?.sort) searchParams.set("sort", params.sort);
  if (params?.order) searchParams.set("order", params.order);
  if (params?.search) searchParams.set("search", params.search);
  const qs = searchParams.toString();
  return fetchJSON<FeaturesResponse>(`/api/results/features${qs ? `?${qs}` : ""}`);
}

export function getFeaturesDownloadUrl(): string {
  return `${API_BASE}/api/results/features/download`;
}

export async function getIssues(): Promise<{ issues: string | null; message?: string }> {
  return fetchJSON("/api/results/issues");
}

/* ── Logs ── */

export async function getLogRuns(): Promise<LogRun[]> {
  const data = await fetchJSON<{ runs: LogRun[] }>("/api/logs/runs");
  return data.runs;
}

export async function getLogFiles(runId: string): Promise<LogFile[]> {
  const data = await fetchJSON<{ files: LogFile[] }>(`/api/logs/${runId}/files`);
  return data.files;
}

export async function getLogFileContent(
  runId: string,
  path: string,
  tail?: number
): Promise<LogFileContent> {
  const params = new URLSearchParams({ path });
  if (tail) params.set("tail", String(tail));
  return fetchJSON<LogFileContent>(`/api/logs/${runId}/file?${params}`);
}

export function getRulegraphUrl(runId: string): string {
  return `${API_BASE}/api/logs/${runId}/rulegraph`;
}

/* ── Dataset ── */

export async function getCurrentDataset(): Promise<DatasetCurrentResponse> {
  return fetchJSON<DatasetCurrentResponse>("/api/dataset/current");
}

export async function getDrives(): Promise<DrivesResponse> {
  return fetchJSON<DrivesResponse>("/api/dataset/drives");
}

export async function browseDataset(path?: string, target?: string): Promise<DatasetBrowseResponse> {
  const params = new URLSearchParams();
  if (path) params.set("path", path);
  if (target) params.set("target", target);
  const qs = params.toString();
  return fetchJSON<DatasetBrowseResponse>(`/api/dataset/browse${qs ? `?${qs}` : ""}`);
}

export async function selectDataset(path: string): Promise<DatasetSelectResponse> {
  return fetchJSON<DatasetSelectResponse>("/api/dataset/select", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path }),
  });
}

export async function selectDatasetByPath(hostPath: string): Promise<DatasetSelectResponse> {
  return fetchJSON<DatasetSelectResponse>("/api/dataset/select-path", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ host_path: hostPath }),
  });
}
