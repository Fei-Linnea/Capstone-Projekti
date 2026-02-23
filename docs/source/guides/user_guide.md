# Local Execution - Quick Start Guide

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
apptainer pull hippocampus-pipeline.sif docker://registry.gitlab.utu.fi/capstone_group_7/radiomic-feature-extraction-hippocampus-morphometry/hippocampus-pipeline
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
| `--help` | Show help message and exit | None | No |
| `--batch-size` | Number of subjects per batch | 5 | No |
| `--cores` | Total CPU cores available to Snakemake. Use `--cores` without a value (or `--cores all`) to use all available CPU cores. | 16 | No |
| `--subjects` | Process specific subjects | all subjects | No |
| `--set-threads` | Override rule threads (e.g., `hsf_segmentation=4`). | 1 except hsf_segmentation=2 | No |
| `--bids-pattern` | BIDS pattern to discover inputs | `sub-*/ses-*/anat/*_T1w.nii.gz` | No |
| `--cleanup` | Remove intermediate files after completion, keeping only `summary/all_features.csv` and error report | disabled | No |
| `--dry-run` | Show what would be done without executing | disabled | No |

**Note:** The `--profile` flag is required to specify default execution settings. Use `config/profiles/tyks` for TYKS environment.

### Performance tuning

Important options:

- `--batch-size`: if you run out of memory or disk space, reduce this first. This controls how many subjects are processed in one batch (i.e., how much intermediate data is created at once).
- `--cores`: set this to the number of CPU cores you are allowed to use. This will use at most N CPU cores/jobs in parallel. If you run `--cores` without a value (or `--cores all`), Snakemake uses all CPU cores available to the machine/container.

Advanced options:

- `--set-threads`: advanced per-rule tuning

Rule of thumb:

- If the run is slow and your CPU is mostly idle, increase `--cores`.
- If the run fails with memory-related errors, decrease `--batch-size`.

**Recommended Settings for Different Machine Sizes:**

| Machine RAM | batch-size | cores | 
|-------------|-----------|--------
| 32 GB       | 10        |  8    |       
| 64 GB       | 20        | 16    |         
| 128 GB      | 40        | 32    |         
| 256 GB      | 80        | 64    |   

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

**Example using a custom BIDS discovery pattern:**
```bash
apptainer run --writable-tmpfs \
  --bind ./DatasetName:/data \
  --bind ./logs:/app/logs \
  hippocampus-pipeline.sif \
  --profile config/profiles/tyks \
  --bids-pattern "sub-*/ses-1/anat/*_T1w.nii.gz"
```

**Example with cores and rule thread override:**
```bash
apptainer run --writable-tmpfs \
  --bind ./DatasetName:/data \
  --bind ./logs:/app/logs \
  hippocampus-pipeline.sif \
  --profile config/profiles/tyks \
  --batch-size 10 \
  --cores 20 \
  --set-threads hsf_segmentation=4 \
```


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
2. Delete intermediate files automatically
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

For comprehensive documentation, see full [Pipeline Guide](pipeline_guide.md).