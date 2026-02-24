/* ── TypeScript interfaces matching the Flask API responses ── */

export interface PipelineDefaults {
  batch_size: number;
  bids_pattern: string;
  data_dir: string;
  log_base_dir: string;
  pipeline_dir: string;
  rule_display_names: Record<string, string>;
  pipeline_config: Record<string, unknown>;
}

export interface ProfileConfig {
  name: string;
  config: Record<string, unknown>;
}

export interface SubjectsResponse {
  subjects: string[];
  count: number;
  bids_pattern: string;
}

export interface PipelineProgress {
  phase: "idle" | "discovering" | "batching" | "aggregating" | "cleaning" | "done";
  batch_num: number;
  total_batches: number;
  current_jobs: number;
  total_jobs: number | null;
  current_rule: string;
  current_subject: string;
  failed_batches: (number | string)[];
  completed_batches: number[];
  subjects_total: number;
}

export interface RunState {
  status: "idle" | "running" | "completed" | "failed" | "cancelling";
  config: PipelineConfig;
  progress: PipelineProgress;
  log_dir: string;
  start_time: string;
  end_time: string;
  error: string;
}

export interface PipelineConfig {
  profile: string;
  batch_size: number;
  cores: number | string | null;
  set_threads: string[] | null;
  subjects: string[] | null;
  bids_pattern: string;
  dry_run: boolean;
  cleanup: boolean;
}

export interface FeaturesResponse {
  columns: string[];
  rows: Record<string, unknown>[];
  total_rows: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface LogRun {
  id: string;
  path: string;
  file_count: number;
}

export interface LogFile {
  name: string;
  path: string;
  size: number;
  size_human: string;
}

export interface LogFileContent {
  run_id: string;
  path: string;
  content: string;
  total_lines: number;
  lines_shown: number;
  truncated: boolean;
}

export interface DatasetCurrentResponse {
  data_dir: string;
  exists: boolean;
  selected_path: string | null;
  subject_count: number;
  subjects: string[];
  total_files: number;
  total_size: number;
  total_size_human: string;
  browse_root: string;
  browse_root_exists: boolean;
}

export interface DatasetEntry {
  name: string;
  path: string;
  type: "file" | "directory";
  size?: number;
  size_human?: string;
  extension?: string;
  child_count?: number;
  has_subjects?: boolean;
}

export interface DatasetBrowseResponse {
  path: string;
  parent: string | null;
  entries: DatasetEntry[];
  total: number;
  is_bids: boolean;
  target: string;
}

export interface DatasetSelectResponse {
  message: string;
  data_dir: string;
  selected_path: string;
  host_path?: string;
  subject_count: number;
  subjects: string[];
}

export interface DriveInfo {
  name: string;
  path: string;
  label: string;
  accessible: boolean;
  child_count: number;
}

export interface DrivesResponse {
  drives: DriveInfo[];
  browse_root: string;
}

export const RULE_DISPLAY_NAMES: Record<string, string> = {
  hsf_segmentation: "HSF Segmentation",
  split_label: "Split Labels",
  mesh_per_label: "Mesh Generation",
  mesh_combined: "Combined Mesh",
  extract_curvature_per_label: "Curvature Extraction",
  extract_curvature_combined: "Combined Curvature",
  extract_pyradiomics_per_label: "PyRadiomics",
  extract_pyradiomics_combined: "Combined PyRadiomics",
  combine_labels: "Combine Labels",
  aggregate_subject_features: "Aggregate Features",
};

export const PHASE_LABELS: Record<string, string> = {
  idle: "Idle",
  discovering: "Discovering Subjects",
  batching: "Processing Batches",
  aggregating: "Aggregating Results",
  cleaning: "Cleaning Up",
  done: "Done",
};
