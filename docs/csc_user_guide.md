# CSC Puhti - Quick Start Guide

## Prerequisites

- A CSC project with access to the Puhti cluster
- BIDS-formatted dataset on `/scratch`
- The pipeline container image (`.sif` file) on `/scratch`

## Setup

### 1. Clone the pipeline repository

```bash
cd /scratch/project_<NUMBER>/$USER
git clone <repo-url> hippocampus-pipeline
cd hippocampus-pipeline/pipeline
```

### 2. Pull the container image

```bash
mkdir -p /scratch/project_<NUMBER>/$USER/Containers
cd /scratch/project_<NUMBER>/$USER/Containers
apptainer pull hippocampus-pipeline.sif docker://docker.io/tarizw/hippocampus-pipeline:v1.0.0
```

This downloads the container image (~4.3 GiB).

## Run the Pipeline

### Interactive mode (recommended for first run)

```bash
python3 run_csc.py
```

The script will prompt you for:
1. **CSC project number** (e.g., `2001988`)
2. **BIDS dataset path** (e.g., `/scratch/project_2001988/user/Dataset`)
3. **Container SIF path** (e.g., `/scratch/project_2001988/user/Containers/hippocampus-pipeline.sif`)
4. **SLURM partition** (default: `small`)

It then shows a configuration summary and asks for confirmation before starting.

### Non-interactive mode

```bash
python3 run_csc.py \
  --project 2001988 \
  --bids-root /scratch/project_2001988/$USER/Dataset \
  --sif /scratch/project_2001988/$USER/Containers/hippocampus-pipeline.sif
```

### Dry run (preview without executing)

```bash
python3 run_csc.py -n
```

## Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--project` | CSC project number | prompted |
| `--bids-root` | BIDS dataset root directory | prompted |
| `--sif` | Path to `.sif` container | prompted |
| `--partition` | SLURM partition | `small` |
| `--jobs` | Max concurrent SLURM jobs | `100` |
| `--latency-wait` | Seconds to wait for output files | `120` |
| `--retries` | Retries per failed job | `1` |
| `-n`, `--dry-run` | Show planned jobs without executing | off |
| `-y`, `--yes` | Skip confirmation prompt | off |
| `--force` | Force re-run all rules | off |
| `--clean` | Remove `.snakemake/` metadata before running | off |

## What the Script Does Automatically

- Loads the `snakemake` module if it is not already available
- Creates a shared temp directory on `/scratch` (SLURM nodes cannot see `/tmp`)
- Clears stale `SINGULARITY_BIND` / `APPTAINER_BIND` variables
- Generates the Snakemake SLURM + Apptainer profile for your project
- Shows a live progress bar during execution

## Output

Results are written to `<bids-root>/derivatives/`:

```
<bids-root>/
  derivatives/
    sub-01/
      ses-1/
        anat/        # Segmentation outputs
        features/    # Extracted radiomic features
        meshes/      # Generated 3D meshes
    sub-02/
      ...
    summary/
      all_features.csv       # Aggregated features from all subjects
      processing_issues.txt  # Any subjects with processing errors
    logs/
      run_csc_<timestamp>.log
```

## Troubleshooting

### Pipeline was interrupted

If you stop the script with `Ctrl+C`, SLURM jobs may still be running. Check and cancel them:

```bash
squeue -u $USER
scancel -u $USER       # cancel all your jobs
```

Then clean stale metadata and re-run:

```bash
python3 run_csc.py --clean
```

### "snakemake not found" error

Load the module manually and retry:

```bash
module load snakemake
python3 run_csc.py
```

### Stale locks or incomplete files

```bash
python3 run_csc.py --clean --force
```

`--clean` removes the `.snakemake/` directory and `--force` re-runs all rules from scratch.
