# CSC Puhti - Quick Start Guide

## Prerequisites

- A CSC project with access to the Puhti cluster
- BIDS-formatted dataset on `/scratch`
- The pipeline container image (`.sif` file) on `/scratch`

## Setup

### 1. Set up Apptainer cache and temp directories (mandatory, one-time)

Apptainer needs a cache and temp directory on shared `/scratch` storage. Add these to your `~/.bashrc` (or run before every session):

```bash
export APPTAINER_CACHEDIR=/scratch/project_<NUMBER>/.apptainer
export APPTAINER_TMPDIR=/scratch/project_<NUMBER>/tmp
export TMPDIR=/scratch/project_<NUMBER>/tmp
mkdir -p $APPTAINER_CACHEDIR $APPTAINER_TMPDIR
```

Replace `<NUMBER>` with your CSC project number (e.g., `2001988`).

**Why this is required:** CSC compute nodes cannot write to `/tmp` or `$HOME` during jobs. The Apptainer cache is used when pulling the container image and the temp directory is used during container execution. Both must be on the shared `/scratch` filesystem.

### 2. Pull the container image

```bash
mkdir -p /scratch/project_<NUMBER>/Containers
cd /scratch/project_<NUMBER>/Containers
apptainer pull hippocampus-pipeline.sif docker://registry.gitlab.utu.fi/capstone_group_7/radiomic-feature-extraction-hippocampus-morphometry/hippocampus-pipeline
```

This downloads the container image (~4.3 GiB). Make sure `APPTAINER_CACHEDIR` and `APPTAINER_TMPDIR` are set (Step 1), otherwise the pull may fail.

### 3. Clone the pipeline repository

```bash
cd /scratch/project_<NUMBER>
module load git
git clone https://gitlab.utu.fi/capstone_group_7/radiomic-feature-extraction-hippocampus-morphometry.git hippocampus-pipeline
cd hippocampus-pipeline/pipeline
```

## Run the Pipeline

### Interactive mode (recommended for first run)

```bash
python3 run_csc.py
```

The script will prompt you for:
1. **CSC project number** (e.g., `2001988`)
2. **BIDS dataset path** (e.g., `/scratch/project_2001988/Dataset`)
3. **BIDS file pattern** (default: `sub-*/ses-*/anat/*_T1w.nii.gz`)
4. **Container SIF path** (e.g., `/scratch/project_2001988/Containers/hippocampus-pipeline.sif`)
5. **SLURM partition** (default: `small`)

It then shows a configuration summary and asks for confirmation before starting.

### Non-interactive mode

```bash
python3 run_csc.py \
  --project <NUMBER> \
  --bids-root /scratch/project_<NUMBER>/$USER/Dataset \
  --sif /scratch/project_<NUMBER>/$USER/Containers/hippocampus-pipeline.sif
```

### Non-interactive mode with rule thread overrides

```bash
python3 run_csc.py \
  --project <NUMBER> \
  --bids-root /scratch/project_<NUMBER>/$USER/Dataset \
  --sif /scratch/project_<NUMBER>/$USER/Containers/hippocampus-pipeline.sif \
  --set-threads hsf_segmentation=4 \
  --set-threads mesh_per_label=2
```

### Dry run (preview without executing)

```bash
python3 run_csc.py -n
```

## Command-Line Options

| Option | Description | Default | Required |
|--------|-------------|---------|----------|
| `--project` | CSC project number (e.g., `2001988`) | prompted | No |
| `--bids-root` | BIDS dataset root directory | prompted | No |
| `--bids-pattern` | Glob pattern (relative to BIDS root) to discover T1w inputs | `sub-*/ses-*/anat/*_T1w.nii.gz` | No |
| `--sif` | Path to `.sif` container image | prompted | No |
| `--partition` | SLURM partition | `small` | No |
| `--jobs` | Max concurrent SLURM jobs | `100` | No |
| `--latency-wait` | Seconds to wait for output files | `120` | No |
| `--retries` | Retries per failed job | `1` | No |
| `--set-threads` | Override rule threads (e.g., `hsf_segmentation=4`). Can be used multiple times. | none | No |
| `-n`, `--dry-run` | Show planned jobs without executing | off | No |
| `-y`, `--yes` | Skip confirmation prompt | off | No |
| `--force` | Force re-run all rules (`--forceall`) | off | No |
| `--clean` | Remove `.snakemake/` metadata before running | off | No |
| `--cleanup` | Delete intermediate outputs after success, keeping summary files and logs | off | No |
| `-h`, `--help` | Show help message and exit | off | No |

**Note:** For interactive mode, run `python3 run_csc.py` with no arguments and provide values when prompted. For non-interactive mode, pass `--project`, `--bids-root`, and `--sif` explicitly.

## What the Script Does Automatically

- Loads the `snakemake` module if it is not already available
- Creates a shared temp directory on `/scratch` (SLURM nodes cannot see `/tmp`)
- Sets `APPTAINER_CACHEDIR` and `APPTAINER_TMPDIR` on `/scratch`
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

### Apptainer pull fails

Make sure cache and tmp directories are set (see Setup Step 1):

```bash
export APPTAINER_CACHEDIR=/scratch/project_<NUMBER>/$USER/.apptainer
export APPTAINER_TMPDIR=/scratch/project_<NUMBER>/$USER/tmp
mkdir -p $APPTAINER_CACHEDIR $APPTAINER_TMPDIR
```
