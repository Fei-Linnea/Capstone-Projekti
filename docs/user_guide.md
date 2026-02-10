# Radiomic Feature Extraction Pipeline - Quick Start Guide

## Prerequisites

- **Apptainer** installed on your system (see [Apptainer installation](https://apptainer.org/docs/admin/main/installation.html))
- BIDS dataset

## Setup

Create an empty logs directory in your project folder:
   ```bash
   mkdir -p logs
   ```

## Download the Pipeline Image

Pull the Apptainer image from Docker Hub:

```bash
apptainer pull hippocampus-pipeline.sif docker://docker.io/tarizw/hippocampus-pipeline:v1.0.0
```

This will download the container image (~4.3 GiB).

## Run the Pipeline

Execute the pipeline with the following command:

```bash
apptainer run --writable-tmpfs \
  --bind {relative or absolute path to BIDS dataset}:/data \
  --bind {path to your logs directory}:/app/logs \
  hippocampus-pipeline.sif \
  --profile config/profiles/tyks \
  --batch-size 10
```

**Example:**
```bash
apptainer run --writable-tmpfs \
  --bind ./DatasetName:/data \
  --bind ./logs:/app/logs \
  hippocampus-pipeline.sif \
  --profile config/profiles/tyks \
  --batch-size 10
```

Or one line command (without backslash):
```bash
apptainer run --writable-tmpfs --bind ./Dataset_Name:/data --bind ./logs:/app/logs hippocampus-pipeline.sif --profile config/profiles/tyks --batch-size 10
```

### Command-Line Options

**Available Pipeline Options:**

| Option | Description | Default | Required |
|--------|-------------|----------|----------|
| `--profile` | Snakemake profile directory (e.g., `config/profiles/tyks`) | None | **Yes** |
| `--batch-size` | Number of subjects per batch | 5 | No |
| `--jobs` | Max parallel Snakemake jobs | 8| No |
| `--cores` | Total CPU cores available to Snakemake | autodetected or 4 | No |
| `--set-threads` | Override rule threads (e.g., `hsf_segmentation=4`) | 1 | No |
| `--cleanup` | Remove intermediate files after completion, keeping only `summary/all_features.csv` and error report | disabled | No |
| `--dry-run` | Show what would be done without executing | disabled | No |
| `--subjects` | Process specific subjects (e.g., `--subjects 01 02 03`) | all subjects | No |

**Note:** The `--profile` flag is required to specify default execution settings. Use `config/profiles/tyks` for TYKS environment.

**Example with cleanup flag:**
```bash
apptainer run --writable-tmpfs \
  --bind ./DatasetName:/data \
  --bind ./logs:/app/logs \
  hippocampus-pipeline.sif \
  --profile config/profiles/tyks \
  --batch-size 10 \
  --cleanup
```

**Example processing specific subjects:**
```bash
apptainer run --writable-tmpfs \
  --bind ./DatasetName:/data \
  --bind ./logs:/app/logs \
  hippocampus-pipeline.sif \
  --profile config/profiles/tyks \
  --subjects 01 02 03 04 05
```

**Example with custom jobs and cores and rule thread override:**
```bash
apptainer run --writable-tmpfs \
  --bind ./DatasetName:/data \
  --bind ./logs:/app/logs \
  hippocampus-pipeline.sif \
  --profile config/profiles/tyks \
  --batch-size 10 \
  --jobs 12 \
  --cores 20 \
  --set-threads hsf_segmentation=4 \
```

**Recommended Settings for Different Machine Sizes:**

| Machine RAM | batch-size | jobs | cores | 
|-------------|-----------|----------------|-----------------|
| 32 GB       | 10        | 4              | 8               | 
| 64 GB       | 20        | 8              | 16              | 
| 128 GB      | 40        | 16             | 32              | 
| 256 GB      | 80        | 32             | 64              |



## Cleanup Option

The `--cleanup` flag removes all intermediate files after successful pipeline completion, keeping only the final `summary/all_features.csv` file and error report. 

**What gets deleted:**
- Individual subject segmentation files (`sub-XX/ses-X/anat/`)
- Per-subject feature files (`sub-XX/ses-X/features/`)
- Mesh files (`sub-XX/ses-X/meshes/`)

**What gets preserved:**
- `derivatives/summary/all_features.csv` (final aggregated results)
- `derivatives/summary/processing_issues.txt` (error report)


**Usage:**
```bash
apptainer run --writable-tmpfs \
  --bind ./DatasetName:/data \
  --bind ./logs:/app/logs \
  hippocampus-pipeline.sif \
  --profile config/profiles/tyks \
  --batch-size 10 \
  --cleanup
```

The cleanup will:
1. Show a preview of what will be deleted
2. Ask for confirmation before proceeding
3. Only run if the pipeline completes successfully

## Output Structure

After successful execution, your dataset directory will contain:

**Without `--cleanup` flag (default):**
```
dataset/
├── derivatives/
│   ├── sub-01/
│   │   └── ses-1/
│   │       ├── anat/          # Segmentation outputs
│   │       ├── features/      # Extracted radiomics features
│   │       └── meshes/        # Generated 3D meshes
│   ├── sub-02/
│   │   └── ...
│   └── summary/
│       ├── all_features.csv       # Aggregated features from all subjects
│       └── processing_issues.txt  # Any subjects with processing errors
```

**With `--cleanup` flag:**
```
dataset/
└── derivatives/
    └── summary/
        ├── all_features.csv       # Aggregated features from all subjects
        └── processing_issues.txt  # Any subjects with processing errors
```

Your logs directory will contain timestamped directories with detailed execution logs:

```
└── logs/
    ├── <timestamp>/
      ├── hsf/                         # Step 1 logs
      ├── data_processing/             # Step 2 logs
      ├── mesh/                        # Step 3 logs
      ├── feature_extraction/          # Steps 4-6 logs
      ├── benchmarks/                # Performance metrics
      │   ├── hsf/
      │   ├── data_processing/
      │   ├── mesh/
      │   └── feature_extraction/
      ├── snakemake_batch_001.log
      └── snakemake_aggregation.log
```

---

For comprehensive documentation, see [pipeline_guide.md](pipeline_guide.md).
